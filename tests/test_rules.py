# Check the fit arithmetic with made-up points and strap masks, not photos.
import copy
import unittest

import numpy as np

from app.core.rules import chest_clip, evaluate, harness_height, lap_belt, shoulder_belt


def pose():
    xy = {"left_shoulder": (50, 50), "right_shoulder": (150, 50),
          "left_elbow": (50, 100), "right_elbow": (150, 100),
          "left_hip": (70, 150), "right_hip": (130, 150)}
    return {"detected": True, "people": 1, "width": 240, "height": 260,
            "points": {n: {"x": x, "y": y, "score": 0.9} for n, (x, y) in xy.items()}}


def item(x, y, horizontal=False):
    mask = np.zeros((260, 240), dtype=bool)
    if horizontal:
        mask[y-2:y+3, 60:141] = True
    else:
        mask[30:190, x-1:x+2] = True
    return {"mask": mask, "tap": [x, y], "confirmed": True, "entry_visible": True}


class RulesTest(unittest.TestCase):
    def test_clip_at_proxy_and_low_high(self):
        for y, expected in [(62, "looks_right"), (73, "issue"), (40, "issue")]:
            with self.subTest(y=y):
                self.assertEqual(chest_clip(pose(), {"clip": item(100, y)})["status"], expected)

    def test_clip_exact_tolerance(self):
        # The armpit guess is y=62.5 and the shoulder width unit is 100px, so 10px is the limit.
        record = item(100, 72)
        record["tap"][1] = 72.5
        value = chest_clip(pose(), {"clip": record})
        self.assertAlmostEqual(value["measured_value"]["delta"], 0.10)
        self.assertEqual(value["status"], "looks_right")

    def test_rear_and_forward_strap_directions(self):
        for seat, y, expected in [("rear", 40, "issue"), ("rear", 60, "looks_right"),
                                  ("forward", 60, "issue"), ("forward", 40, "looks_right")]:
            with self.subTest(seat=seat, y=y):
                record = item(50, y)
                self.assertEqual(harness_height(pose(), {"strap_left": record}, seat, "left")["status"], expected)

    def test_hidden_entry_abstains(self):
        record = item(50, 50)
        record["entry_visible"] = False
        self.assertEqual(harness_height(pose(), {"strap_left": record}, "rear", "left")["status"], "cannot_check")

    def test_shoulder_belt_positions(self):
        for x, expected in [(70, "looks_right"), (130, "looks_right"), (100, "issue"), (165, "issue")]:
            with self.subTest(x=x):
                self.assertEqual(shoulder_belt(pose(), {"shoulder_belt": item(x, 80)})["status"], expected)

    def test_shoulder_missing_or_broad_crossing_abstains(self):
        record = item(70, 80)
        record["mask"][:60] = False
        self.assertEqual(shoulder_belt(pose(), {"shoulder_belt": record})["status"], "cannot_check")
        record["mask"][45:55, 30:180] = True
        self.assertEqual(shoulder_belt(pose(), {"shoulder_belt": record})["status"], "cannot_check")

    def test_lap_hip_belly_and_too_low(self):
        for y, expected in [(160, "looks_right"), (125, "issue"), (180, "issue")]:
            with self.subTest(y=y):
                self.assertEqual(lap_belt(pose(), {"lap_belt": item(100, y, True)})["status"], expected)

    def test_unconfirmed_empty_outside_and_wrong_size_abstain(self):
        examples = [item(100, 62) for _ in range(4)]
        examples[0]["confirmed"] = False
        examples[1]["mask"][:] = False
        examples[2]["tap"] = [-1, 62]
        examples[3]["mask"] = np.ones((10, 10), bool)
        for record in examples:
            self.assertEqual(chest_clip(pose(), {"clip": record})["status"], "cannot_check")

    def test_uncertain_or_multiple_people_abstain(self):
        for change in ["confidence", "missing", "multiple", "not_detected"]:
            p = pose()
            if change == "confidence":
                p["points"]["left_shoulder"]["score"] = .49
            if change == "missing":
                del p["points"]["left_hip"]
            if change == "multiple":
                p["people"] = 2
            if change == "not_detected":
                p["detected"] = False
            self.assertEqual(chest_clip(p, {"clip": item(100, 62)})["status"], "cannot_check")

    def test_degenerate_or_nan_body_abstains(self):
        for bad in [float("nan"), 150, -10, 500]:
            p = pose()
            p["points"]["left_shoulder"]["x"] = bad
            self.assertEqual(chest_clip(p, {"clip": item(100, 62)})["status"], "cannot_check")

    def test_scale_and_translation_invariance(self):
        p, record = pose(), item(70, 80)
        expected = shoulder_belt(p, {"shoulder_belt": record})
        q = copy.deepcopy(p)
        q.update(width=p["width"]*2+20, height=p["height"]*2+20)
        for point in q["points"].values():
            point.update(x=point["x"]*2+10, y=point["y"]*2+10)
        large = np.zeros((q["height"], q["width"]), bool)
        large[10:530, 10:490] = np.repeat(np.repeat(record["mask"], 2, axis=0), 2, axis=1)
        result = shoulder_belt(q, {"shoulder_belt": {**record, "mask": large, "tap": [150, 170]}})
        self.assertEqual(result["status"], expected["status"])
        self.assertAlmostEqual(result["measured_value"]["crossing_ratio"], expected["measured_value"]["crossing_ratio"], delta=.003)

    def test_rotation_invariance(self):
        p, record = pose(), item(100, 90)
        expected = chest_clip(p, {"clip": record})
        q = copy.deepcopy(p)
        q.update(width=p["height"], height=p["width"])
        for point in q["points"].values():
            point.update(x=p["height"]-1-point["y"], y=point["x"])
        turned = {**record, "mask": np.rot90(record["mask"], -1), "tap": [p["height"]-1-90, 100]}
        result = chest_clip(q, {"clip": turned})
        self.assertEqual(result["status"], expected["status"])
        self.assertAlmostEqual(result["measured_value"]["delta"], expected["measured_value"]["delta"])

    def test_applicable_checks_manual_cards_and_unvalidated_flags(self):
        checks = evaluate(pose(), {}, "rear")
        self.assertEqual(len(checks), 8)
        self.assertEqual(len(evaluate(pose(), {}, "booster")), 7)
        self.assertTrue(all(c["status"] == "cannot_check" for c in checks))
        self.assertTrue(all(c["threshold"]["validated"] is False for c in checks))
        with self.assertRaises(ValueError):
            evaluate(pose(), {}, "unknown")


if __name__ == "__main__":
    unittest.main()
