"""Taps guide the strap mask. We drop the photo features after each call."""
from pathlib import Path
from threading import Lock

import numpy as np
import requests
import torch

from app.core.mask_quality import CUTOFFS, rejection
from app.core.rules import references

_predictors = {}
_lock = Lock()
ROOT = Path(__file__).resolve().parents[2]
MOBILE_COMMIT = "f706ad9c4eb7f219c00d9050e46328518ffb65d2"

# WHY: these UNVALIDATED shape guesses were set before the drawing tests, not from fit results.
SELECTION = dict(validated=False, min_length_shoulder_fraction=0.10, min_strap_aspect=2., max_clip_aspect=3.)


def select_mask(masks, scores, taps, keypoints, item):
    """Reject body-sized masks first. A thin shape or high score still needs a person to confirm it."""
    ref=references(keypoints)
    preferred=[];eligible=[]
    for index,raw in enumerate(masks):
        mask=np.asarray(raw,dtype=bool)
        if rejection(mask,keypoints,item) is not None:continue
        # WHY: a thin mask elsewhere in the photo is useless; it still has to follow the taps.
        if any(bool(mask[int(t['y']),int(t['x'])]) != bool(t.get('label',1)) for t in taps):continue
        y,x=np.nonzero(mask);xy=np.column_stack([x,y]).astype(float);xy-=xy.mean(axis=0)
        _,axes=np.linalg.eigh(xy.T@xy/len(xy))
        minor,major=np.sort(np.ptp(xy@axes,axis=0)+1.)
        aspect=major/minor;score=float(scores[index])
        if not np.isfinite(score):score=-np.inf
        eligible.append((score,-index,index))
        if item=='clip':
            if aspect<=SELECTION['max_clip_aspect']:preferred.append((-len(x),-aspect,score,-index,index))
        elif (major>=SELECTION['min_length_shoulder_fraction']*ref[1] and
              minor<=CUTOFFS['max_minor_shoulder_fraction']*ref[1] and aspect>=SELECTION['min_strap_aspect']):
            preferred.append((aspect,-minor,score,-index,index))
    chosen=max(preferred)[-1] if preferred else max(eligible)[-1] if eligible else None
    # WHY: nothing passed, so an empty strap mask sends the parent back to retap.
    return np.asarray(masks[chosen],dtype=bool) if chosen is not None else np.zeros_like(masks[0],dtype=bool)


def segment(image, taps, model="mobile_sam", *, keypoints=None, item_type=None):
    """Label 1 means include this point, 0 means avoid it. The parent still confirms the strap mask."""
    if model not in ("mobile_sam", "sam") or not taps:
        raise ValueError("Choose a supported model and at least one tap.")
    height, width = image.shape[:2]
    points = np.array([[p["x"], p["y"]] for p in taps], dtype=float)
    labels = np.array([p.get("label", 1) for p in taps])
    if (not np.isfinite(points).all() or (points < 0).any() or
            (points[:, 0] >= width).any() or (points[:, 1] >= height).any() or
            not set(labels).issubset({0, 1}) or 1 not in labels):
        raise ValueError("Tap inside the photo.")
    with _lock:
        if model not in _predictors:
            if model == "mobile_sam":
                from mobile_sam import SamPredictor, sam_model_registry
                name, kind = "mobile_sam.pt", "vit_t"
                url = f"https://raw.githubusercontent.com/ChaoningZhang/MobileSAM/{MOBILE_COMMIT}/weights/{name}"
            else:
                from segment_anything import SamPredictor, sam_model_registry
                name, kind = "sam_vit_b_01ec64.pth", "vit_b"
                url = "https://dl.fbaipublicfiles.com/segment_anything/"+name
            path = ROOT / ".venv/models" / name
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with requests.get(url, stream=True, timeout=120) as response:
                    response.raise_for_status()
                    with path.with_suffix(".part").open("wb") as handle:
                        for chunk in response.iter_content(1024*1024):
                            handle.write(chunk)
                path.with_suffix(".part").replace(path)
            torch.set_num_threads(4)
            _predictors[model] = SamPredictor(sam_model_registry[kind](checkpoint=str(path)).to("cpu").eval())
        predictor = _predictors[model]
        try:
            with torch.inference_mode():
                predictor.set_image(image)
                masks, scores, _ = predictor.predict(point_coords=points, point_labels=labels, multimask_output=True)
            if item_type is not None:
                return select_mask(masks,scores,taps,keypoints or {},item_type)
            # WHY: warmup has no item or body points; actual taps go through the mask picker above.
            return masks[int(np.argmax(scores))].astype(bool)
        finally:
            predictor.reset_image()  # WHY: drop the cached photo features, even if prediction failed.
