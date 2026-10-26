"""Group saved sessions by car so one car cannot end up in two splits."""
import argparse
import json
from pathlib import Path
import random
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def tagged_sessions(root):
    """Use the saved split field. A filename cannot tell us which split someone intended."""
    rows, cars = [], {}
    for path in sorted(Path(root).glob("*/annotations.json")):
        meta = json.loads(path.read_text())["info"]["metadata"]
        if meta.get("split") not in ("train", "test"):
            raise ValueError(f"Required split must be train or test: {path}")
        car = meta.get("car_id")
        if not car or meta.get("consent") != "Y" or meta.get("session_id") != path.parent.name:
            raise ValueError(f"Missing consent or inconsistent session/car: {path}")
        if car in cars and cars[car] != meta["split"]:
            raise ValueError(f"car_id {car} appears in both train and test splits.")
        cars[car] = meta["split"]
        rows.append((path, meta))
    return rows


def split(root, seed=42):
    from app.labeling import reject_test_photo
    groups, tags = {}, {}
    for path, meta in tagged_sessions(root):
        data = json.loads(path.read_text())
        car = meta["car_id"]
        tags[car] = meta["split"]
        for image in data["images"]:
            with Image.open(path.parent/image["file_name"]) as source:
                reject_test_photo(np.array(source.convert("RGB")))
        groups.setdefault(car, []).append(str(path))
    cars = sorted(car for car in groups if tags[car] == "train")
    random.Random(seed).shuffle(cars)
    count = len(cars)
    # WHY: take validation cars only from the train split; do not quietly move a test car into it.
    val = max(1, round(count*0.2)) if count >= 2 else 0
    assignment = {"train": cars[val:], "val": cars[:val],
                  "test": sorted(car for car in groups if tags[car] == "test")}
    return {"seed": seed, "group_by": "car_id across all sessions", "car_groups": assignment,
        "warnings": (["Need at least two train-tagged cars for car-disjoint early-stopping validation."] if count < 2 else [])+
                    ([] if assignment["test"] else ["No explicitly test-tagged car is available."]),
        "splits": {name: [p for car in group for p in groups[car]] for name, group in assignment.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="data/labeled")
    parser.add_argument("--output", default="data/splits.json")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = split(args.root, args.seed)
    Path(args.output).write_text(json.dumps(result, indent=2)+"\n")
    print({name: len(rows) for name, rows in result["splits"].items()}, result["warnings"])
