"""Photos get saved only through this labeling path, after recorded consent."""
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re
from uuid import uuid4
from threading import Lock

import numpy as np
from PIL import Image

from app.core.pose import NAMES
from data.setup_codes import VALID_SETUPS

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ["clip", "strap_left", "strap_right", "shoulder_belt", "lap_belt"]
SAVE_LOCK = Lock()


def fingerprint(image):
    small = np.array(Image.fromarray(image).convert("L").resize((9, 8)))
    return (small[:, 1:] > small[:, :-1]).ravel()


@lru_cache(maxsize=1)
def held_out_fingerprints():
    # WHY: a renamed or resized TEST photo is still TEST, so filenames are not enough.
    # WHY: stored fingerprints still catch those photos when the ignored originals are not here.
    signatures = json.loads((ROOT/"app/held_out_fingerprints.json").read_text())
    return [np.array([bit == "1" for bit in row["difference_hash"]]) for row in signatures]


def reject_test_photo(image):
    candidates = (fingerprint(image), fingerprint(image[:, ::-1]))
    if any(np.count_nonzero(candidate != known) <= 4 for candidate in candidates for known in held_out_fingerprints()):
        raise ValueError("This matches a held-out kill-test photo. It cannot enter the labeling dataset.")


def rle(mask):
    # WHY: COCO counts mask pixels down columns, starting with a run of background pixels.
    flat = mask.astype(np.uint8).ravel(order="F")
    edges = np.r_[0, np.flatnonzero(np.diff(flat))+1, len(flat)]
    counts = np.diff(edges).tolist()
    if flat[0]:
        counts.insert(0, 0)
    return {"size": list(mask.shape), "counts": counts}


def save_session(image, masks, keypoints, metadata, root=None, receipt=False):
    # WHY: two saves at once must not put the same car in both train and test.
    with SAVE_LOCK:
        session = _save_session(image, masks, keypoints, metadata, root)
        if receipt:
            from data.split import tagged_sessions
            # WHY: count on the server so refreshing the phone, or using another phone, does not reset it.
            return dict(session_id=session, count=len(tagged_sessions(root or ROOT/"data/labeled")))
        return session


def _save_session(image, masks, keypoints, metadata, root=None):
    reject_test_photo(image)
    if metadata.get("consent") != "Y":
        raise ValueError("Recorded consent=Y is required before saving.")
    if metadata.get("split") not in ("train", "test"):
        raise ValueError("Choose a required split: train or test.")
    if metadata.get("deliberate_mistake") not in VALID_SETUPS:
        raise ValueError("Choose a setup code: B1–B10, H1–H9 or other.")
    clean = {}
    for name in ("car_id", "seat_id", "subject_id", "lighting", "deliberate_mistake", "seat_type"):
        value = str(metadata.get(name, "")).strip()
        if not value or len(value) > 80:
            raise ValueError(f"Provide {name} (80 characters or fewer).")
        if name.endswith("_id") and not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("Use letters, numbers, underscores or hyphens for dataset IDs.")
        clean[name] = value
    if not masks:
        raise ValueError("Confirm at least one mask before saving labels.")
    session = uuid4().hex
    clean.update(session_id=session, consent="Y", split=metadata["split"])
    from data.split import tagged_sessions
    for _, existing in tagged_sessions(root or ROOT/"data/labeled"):
        if existing["car_id"] == clean["car_id"] and existing["split"] != clean["split"]:
            raise ValueError("This car_id already belongs to the other split; a car cannot be both train and test.")
    annotations = []
    joints = []
    for name in NAMES:
        point = keypoints.get("points", {}).get(name)
        joints.extend([point["x"], point["y"], 2 if point["score"] >= 0.5 else 1] if point else [0, 0, 0])
    for name, record in masks.items():
        if record.get("confirmed") is not True or name not in CATEGORIES:
            raise ValueError("Only confirmed known items can be saved.")
        mask = record["mask"]
        if mask.shape != image.shape[:2]:
            raise ValueError("Label masks must match the photo.")
        y, x = np.nonzero(mask)
        if not len(x):
            raise ValueError("Empty masks cannot be labels.")
        annotations.append({"id": len(annotations)+1, "image_id": 1, "category_id": CATEGORIES.index(name)+1,
            "segmentation": rle(mask), "area": int(mask.sum()), "iscrowd": 0,
            "bbox": [int(x.min()), int(y.min()), int(x.max()-x.min()+1), int(y.max()-y.min()+1)],
            "keypoints": joints, "num_keypoints": sum(joints[i] > 0 for i in range(2, len(joints), 3)),
            "taps": [record["tap"]], "confirmed": True, "entry_visible": record["entry_visible"]})
    destination = Path(root or ROOT/"data/labeled")/session
    destination.mkdir(parents=True, exist_ok=False)
    Image.fromarray(image).save(destination/"image.jpg", quality=95)  # leave out EXIF, including location metadata
    for name, record in masks.items():
        Image.fromarray(record["mask"].astype(np.uint8)*255).save(destination/(name+".png"))
    data = {"info": {"metadata": clean, "keypoints": keypoints,
                     "keypoints_provenance": "RTMPose predictions; visibility codes use confidence, not manual visibility labels",
                     "mask_provenance": "human-confirmed SAM outline; review before training"},
        "images": [{"id": 1, "file_name": "image.jpg", "width": image.shape[1], "height": image.shape[0],
                    "source_pixel_sha256": sha256(image.tobytes()).hexdigest()}],
        "annotations": annotations, "categories": [{"id": i+1, "name": n, "keypoints": NAMES} for i, n in enumerate(CATEGORIES)]}
    (destination/"annotations.json").write_text(json.dumps(data, indent=2)+"\n")
    return session
