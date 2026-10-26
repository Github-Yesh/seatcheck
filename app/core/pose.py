"""Turn the photo into named body points in memory. The rest of the app can swap pose models."""
from threading import Lock

import cv2
import numpy as np
from rtmlib import Body

_model = None
_lock = Lock()
NAMES = ["nose", "left_eye", "right_eye", "left_ear", "right_ear", "left_shoulder",
         "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
         "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]


def get_keypoints(image):
    """Use the largest detected person, but report the count so the app can flag extra people."""
    global _model
    height, width = image.shape[:2]
    result = {"detected": False, "people": 0, "width": width, "height": height, "points": {}}
    with _lock:
        if _model is None:
            _model = Body(mode="balanced", backend="onnxruntime", device="cpu")
        # WHY: RTMPose wants BGR color order; the browser and Pillow give us RGB.
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        boxes = _model.det_model(bgr)
        if not len(boxes):
            return result  # WHY: don't let rtmlib guess a body across the whole photo when nobody was detected.
        areas = (boxes[:, 2]-boxes[:, 0])*(boxes[:, 3]-boxes[:, 1])
        box = boxes[int(np.argmax(areas))]
        points, scores = _model.pose_model(bgr, bboxes=[box])
    result.update(detected=True, people=len(boxes))
    for name, point, score in zip(NAMES, points[0], scores[0]):
        if np.isfinite([*point, score]).all():
            result["points"][name] = {"x": float(point[0]), "y": float(point[1]), "score": float(score)}
    return result
