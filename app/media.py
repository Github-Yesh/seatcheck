"""Decode photos and carry strap masks as PNGs in memory."""
import base64
from io import BytesIO

import numpy as np
from PIL import Image, ImageOps


def image_from_data(value):
    # WHY: fix orientation in memory so the photo, taps, and strap mask share the same pixel grid.
    raw = base64.b64decode(value.split(",")[-1], validate=True)
    with Image.open(BytesIO(raw)) as source:
        if source.width*source.height > 16_000_000:
            raise ValueError("Choose a smaller photo.")
        return np.array(ImageOps.exif_transpose(source).convert("RGB"))


def png_data(array):
    stream = BytesIO()
    Image.fromarray(array).save(stream, format="PNG")
    return "data:image/png;base64,"+base64.b64encode(stream.getvalue()).decode()


def decode_masks(records, shape):
    result = {}
    for name, record in records.items():
        if name not in ("clip", "strap_left", "strap_right", "shoulder_belt", "lap_belt"):
            raise ValueError("Unknown tapped item.")
        if record.get("confirmed") is not True:
            continue
        mask = image_from_data(record["png"])
        if mask.shape[:2] != shape[:2]:
            raise ValueError("The mask must match this photo.")
        result[name] = {"mask": mask[:, :, 0] > 0, "tap": record["tap"],
                        "confirmed": True, "entry_visible": record.get("entry_visible", False)}
    return result
