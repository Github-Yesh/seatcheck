"""The quality gate stops weak photo evidence before fit checks. Its cutoffs are UNVALIDATED."""
import numpy as np

from app.core.rules import evaluate

# WHY: these are UNVALIDATED engineering guesses, not numbers fitted to photos or clinical guidance.
CUTOFFS = dict(min_short_edge_px=128, min_mean_luma=32, min_landmark_score=0.70,
               context_shoulder_fraction=0.25, min_context_px=2)
GROUPS = {"shoulders": ("left_shoulder", "right_shoulder"),
          "hips": ("left_hip", "right_hip"), "elbows": ("left_elbow", "right_elbow")}


def image_reason(image):
    if min(image.shape[:2]) < CUTOFFS["min_short_edge_px"]:
        return "Photo too small. Use a larger, original photo."
    luma = float(np.mean(image, axis=(0, 1)) @ np.array([.2126, .7152, .0722]))
    if luma < CUTOFFS["min_mean_luma"]:
        return "Photo too dark. Retake it in brighter light."
    return None


def landmark_reason(image, keypoints, groups):
    height, width = image.shape[:2]
    points = keypoints.get("points", {})
    if not keypoints.get("detected") or keypoints.get("people") != 1:
        return "Body points are unclear. Show one child with shoulders and hips in the photo."
    if (keypoints.get("height"), keypoints.get("width")) != (height, width):
        return "Body points do not match this photo. Choose the photo again."
    left, right = (points.get(name, {}) for name in GROUPS["shoulders"])
    span = np.hypot(right.get("x", np.nan)-left.get("x", np.nan),
                    right.get("y", np.nan)-left.get("y", np.nan))
    margin = max(CUTOFFS["min_context_px"], float(span)*CUTOFFS["context_shoulder_fraction"]) if np.isfinite(span) else CUTOFFS["min_context_px"]
    for group in groups:
        for name in GROUPS[group]:
            point = points.get(name, {})
            values = np.array([point.get("x", np.nan), point.get("y", np.nan), point.get("score", 0)])
            if not np.isfinite(values).all() or not (0 <= values[0] < width and 0 <= values[1] < height):
                return group.capitalize()+" are not in the photo. Include them fully."
            if values[2] < CUTOFFS["min_landmark_score"]:
                return group.capitalize()+" are unclear in the photo. Retake a clear photo."
            if not (margin <= values[0] < width-margin and margin <= values[1] < height-margin):
                return group.capitalize()+" are too close to the photo edge. Include them fully."
    return None


def evaluate_photo(image, keypoints, masks, seat_type):
    reason = image_reason(image)
    # WHY: a dark or tiny photo should not give a fit verdict; the hand check cards stay as they are.
    checks = evaluate({} if reason else keypoints, masks, seat_type)
    for check in checks:
        if check["threshold"].get("photo_measurement") is False:
            continue
        needed = ("shoulders", "hips", "elbows") if check["check"] == "chest_clip" else ("shoulders", "hips")
        blocked = reason or landmark_reason(image, keypoints, needed)
        if blocked:
            check.update(status="cannot_check", measured_value=None,
                         explanation=blocked+" Photo-quality cutoffs are UNVALIDATED.",
                         quality_gate=dict(validated=False, cutoffs=dict(CUTOFFS)))
    return checks
