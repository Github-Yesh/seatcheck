"""Suggest five tap positions using fixed MobileNet features and small heatmaps."""
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torch import nn
from torchvision.models import mobilenet_v3_small, MobileNet_V3_Small_Weights

ROOT = Path(__file__).resolve().parents[1]
NAMES = ("clip", "strap_left", "strap_right", "shoulder_belt", "lap_belt")
ARCH = "mobilenet_v3_small_stride16_heatmaps_v1"
MIN_CONFIDENCE = 0.3  # WHY: this UNVALIDATED heatmap cutoff is not a chance that the suggestion is right.


class TapModel(nn.Module):
    def __init__(self, pretrained=False):
        super().__init__()
        torch.hub.set_dir(str(ROOT/".venv/models/torch"))
        weights = MobileNet_V3_Small_Weights.IMAGENET1K_V1 if pretrained else None
        self.features = mobilenet_v3_small(weights=weights).features[:9]
        self.features.requires_grad_(False)
        self.head = nn.Sequential(nn.Conv2d(48, 64, 3, padding=1), nn.ReLU(),
                                  nn.Upsample(scale_factor=4, mode="bilinear", align_corners=False),
                                  nn.Conv2d(64, len(NAMES), 1))

    def train(self, mode=True):
        super().train(mode)
        self.features.eval()  # WHY: keep the pretrained batch statistics fixed too; small batches can otherwise shift them.
        return self

    def forward(self, image):
        with torch.no_grad():
            features = self.features(image)
        return self.head(features)


def tensor_image(image, size):
    values = np.array(image.convert("RGB").resize((size, size), Image.Resampling.BILINEAR), copy=True)
    tensor = torch.from_numpy(values).permute(2, 0, 1).float()/255
    return (tensor-torch.tensor([.485, .456, .406])[:, None, None])/torch.tensor([.229, .224, .225])[:, None, None]


def heatmap_loss(logits, target, visible):
    weight = (1+20*target)*visible[:, :, None, None]
    # WHY: a skipped item is unknown, not proof that there is no strap or clip there.
    return ((logits.sigmoid()-target).square()*weight).sum()/weight.sum().clamp_min(1)


def load_checkpoint(path, allow_smoke=False):
    data = torch.load(path, map_location="cpu", weights_only=True)
    if data.get("architecture") != ARCH or data.get("names") != list(NAMES) or not data.get("trained"):
        raise ValueError("Unsupported or untrained tap checkpoint.")
    if data.get("synthetic_smoke") is not False and not allow_smoke:
        raise ValueError("Synthetic smoke checkpoints cannot enable app suggestions.")
    if data.get("epochs_completed", 0) < 1 or len(data.get("label_counts", [])) != len(NAMES):
        raise ValueError("Checkpoint is missing training provenance.")
    size = data.get("input_size", 0)
    counts = data["label_counts"]
    if type(size) is not int or size < 64 or size % 16 or any(type(n) is not int or n < 0 for n in counts) or not any(counts):
        raise ValueError("Invalid checkpoint dimensions or label counts.")
    model = TapModel().eval()
    model.load_state_dict(data["state_dict"], strict=True)
    return model, data


def predict(model, image, size, label_counts):
    if not isinstance(image, Image.Image):
        image = Image.fromarray(np.asarray(image, dtype=np.uint8))
    width, height = image.size
    with torch.inference_mode():
        maps = model(tensor_image(image, size)[None]).sigmoid()[0]
    result = {}
    for index, name in enumerate(NAMES):
        if not label_counts[index]:
            continue
        heatmap = maps[index]
        flat = int(heatmap.argmax())
        y, x = divmod(flat, heatmap.shape[1])
        score = float(heatmap[y, x])
        if score < MIN_CONFIDENCE:
            continue
        result[name] = dict(x=x/(heatmap.shape[1]-1)*(width-1), y=y/(heatmap.shape[0]-1)*(height-1), confidence=score)
    return result
