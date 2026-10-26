"""Optional suggested taps. We only load the checkpoint someone explicitly chose."""
from threading import Lock

from app.core.rules import references


def load_predictor(path):
    if not path:
        raise ValueError("--suggestions requires --tap-checkpoint from a real labeled training run.")
    # WHY: plain tap mode should not load an extra model or start downloading weights.
    from train.model import load_checkpoint
    model, metadata = load_checkpoint(path)
    from scripts.validation_bar import receipt_ok
    if not receipt_ok(path):
        raise ValueError("Suggestions OFF: checkpoint has not met the pre-registered validation-car bar.")
    return model, metadata, Lock()


def suggest_taps(image, keypoints, predictor=None):
    """The score ranks suggestions, not accuracy. No explicitly enabled model means no suggestions."""
    if predictor is None or references(keypoints) is None:
        return {}
    from train.model import predict
    model, metadata, lock = predictor
    with lock:
        return predict(model, image, metadata["input_size"], metadata["label_counts"])
