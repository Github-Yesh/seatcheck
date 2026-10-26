"""Fit measurements in the shoulder width unit. The numbers and body guesses are UNVALIDATED."""
import numpy as np

SOURCE = "https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Car-Safety-Seats-Information-for-Families.aspx"
INSPECTION = "https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats#installation-help-inspection"
# WHY: link the guidance we actually opened; our photo cutoffs do not come from those sources.
OFFICIAL_SOURCES = {
    "aap": ("AAP HealthyChildren.org", SOURCE),
    "rear": ("NHTSA", "https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-rear-facing-car-seats"),
    "forward": ("NHTSA", "https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-forward-facing-car-seats"),
    "belts": ("NHTSA", "https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats"),
    "recalls": ("NHTSA", "https://www.nhtsa.gov/car-seats-and-booster-seats/used-car-seat-safety-checklist"),
}
# Guidance is paraphrased. The sources and our separate number guesses are in docs/RULE_SOURCES.md.
RULE_SOURCES = {
    "chest_clip": ("Position the chest clip level with the child's armpits.", "forward", "Fitting Your Child Correctly in the Car Seat, step 4"),
    "harness_entry_rear": ("Use harness slots level with or lower than the shoulders when rear-facing.", "rear", "Fitting Your Child Correctly in the Car Seat, step 2"),
    "harness_entry_forward": ("For forward-facing, route harness straps through slots at shoulder height or higher.", "forward", "Fitting Your Child Correctly in the Car Seat, step 2"),
    "shoulder_belt": ("Position the shoulder belt across shoulder and chest, away from neck and face.", "belts", "Types and Recommendations: Booster Seat / Seat Belt, ages 8–12"),
    "lap_belt": ("Keep the lap belt snug over the upper thighs, rather than the stomach.", "belts", "Types and Recommendations: Booster Seat / Seat Belt, ages 8–12"),
    "installation_tightness": ("For an installed harness seat, test sideways and fore/aft belt-path movement against the one-inch limit.", "aap", "Installation tips for rear-facing car seats"),
    "pinch_test": ("Adjust the harness until no extra strap material can be pinched at the shoulder.", "forward", "Fitting Your Child Correctly in the Car Seat, step 3"),
    "recline": ("Follow the seat's recline instructions and use its angle indicator if provided.", "rear", "Installing a Car Seat with a Seat Belt, step 7"),
    "expiration": ("Read the manufacture-date label and ask the seat maker about its usable lifespan.", "aap", "Shopping for car safety seats: Never use a car seat that is too old"),
    "recalls": ("Use the seat's model number and manufacture date to check recalls, consulting its maker if recalled.", "recalls", "Used Car Seat Safety Checklist: labels and recalls"),
}
SEATS = ("rear", "forward", "booster")
THRESHOLDS = {
    "clip": {"absolute_delta_max": 0.10, "armpit_elbow_fraction": 0.25},
    "strap": {"one_sided_tolerance": 0.05},
    "shoulder_belt": {"accepted_bands": [[0.10, 0.30], [0.70, 0.90]], "line_half_band": 0.05, "max_spread": 0.25},
    "lap_belt": {"accepted_band": [-0.05, 0.25], "hip_margin": 0.10, "max_spread": 0.20},
}
MANUAL = {
    "installation_tightness": "Check movement at the belt path by hand using the seat manual; a photo cannot test tightness.",
    "pinch_test": "Check harness slack with the pinch test described in the seat manual; a photo cannot feel tension.",
    "recline": "Read the seat's recline indicator and follow its manual; this photo cannot verify the installed angle.",
    "expiration": "Read the seat's date/expiration label and manual; this photo does not verify its service life.",
    "recalls": "Check the exact model and manufacture date with the manufacturer or NHTSA; this app does not check recalls.",
}


def result(check, status, value, threshold, explanation):
    source_key = check
    if check in ("left_harness_entry", "right_harness_entry"):
        # WHY: rear and forward seats use opposite slot guidance, even when we cannot check the photo.
        source_key = {"at_or_below": "harness_entry_rear", "at_or_above": "harness_entry_forward"}.get(threshold.get("direction"), "missing")
    guidance, reference, section = RULE_SOURCES.get(source_key, ("NEEDS SOURCE", "missing", "NEEDS SOURCE"))
    source_name, url = OFFICIAL_SOURCES.get(reference, ("NEEDS SOURCE", None))
    return {"check": check, "status": status, "measured_value": value,
            "threshold": {**threshold, "units": "not applicable" if threshold.get("photo_measurement") is False else "shoulder widths", "validated": False},
            "explanation": explanation, "source": url, "source_name": source_name,
            "guidance": guidance, "source_section": section}


def references(keypoints, extra=()):
    """Think of the shoulder width unit as a ruler that grows and tilts with the body."""
    if not keypoints.get("detected") or keypoints.get("people") != 1:
        return None
    names = ["left_shoulder", "right_shoulder", "left_hip", "right_hip", *extra]
    points = {}
    for name in names:
        point = keypoints.get("points", {}).get(name, {})
        data = [point.get("x", np.nan), point.get("y", np.nan), point.get("score", 0)]
        if not np.isfinite(data).all() or data[2] < 0.5:
            return None
        if not (0 <= data[0] < keypoints.get("width", 0) and 0 <= data[1] < keypoints.get("height", 0)):
            return None
        points[name] = np.array(data[:2], dtype=float)
    left, right = points["left_shoulder"], points["right_shoulder"]
    width = float(np.linalg.norm(right-left))
    if width < 1e-6:
        return None
    u = (right-left)/width
    v = np.array([-u[1], u[0]])
    hips = (points["left_hip"]+points["right_hip"])/2
    if np.dot(hips-(left+right)/2, v) < 0:
        v = -v
    if abs(np.dot(hips-(left+right)/2, v))/width < 1e-6:
        return None
    return points, width, u, v


def confirmed(record, keypoints):
    if not record or record.get("confirmed") is not True:
        return None
    mask = np.asarray(record.get("mask", []), dtype=bool)
    tap = np.asarray(record.get("tap", []), dtype=float)
    expected = (keypoints.get("height"), keypoints.get("width"))
    if mask.shape != expected or not mask.any() or tap.shape != (2,) or not np.isfinite(tap).all():
        return None
    x, y = tap
    if not (0 <= x < mask.shape[1] and 0 <= y < mask.shape[0]) or not mask[int(y), int(x)]:
        return None
    return mask, tap


def chest_clip(keypoints, masks):
    threshold = THRESHOLDS["clip"]
    ref = references(keypoints, ("left_elbow", "right_elbow"))
    item = confirmed(masks.get("clip"), keypoints)
    if ref is None or item is None:
        return result("chest_clip", "cannot_check", None, threshold,
                      "I need clear body points and a confirmed tap at the clip center. Follow the seat manual and check at armpit level.")
    p, width, _, v = ref
    armpits = [p[s+"_shoulder"]+0.25*(p[s+"_elbow"]-p[s+"_shoulder"]) for s in ("left", "right")]
    # WHY: the center of a whole strap mask is not the clip center, so use the actual clip tap.
    delta = float(np.dot(item[1]-np.mean(armpits, axis=0), v)/width)
    status = "looks_right" if abs(delta) <= 0.10+1e-9 else "issue"
    direction = "below" if delta > 0 else "above"
    text = "Your clip tap is near the estimated armpit line." if status == "looks_right" else f"Your clip tap is {direction} the estimated armpit line. Recheck its height by hand."
    return result("chest_clip", status, {"delta": delta}, threshold, text+" This photo threshold is unvalidated.")


def harness_height(keypoints, masks, seat_type, side):
    threshold = {**THRESHOLDS["strap"], "direction": "at_or_below" if seat_type == "rear" else "at_or_above"}
    check = side+"_harness_entry"
    ref, record = references(keypoints), masks.get("strap_"+side)
    item = confirmed(record, keypoints)
    if ref is None or item is None or record.get("entry_visible") is not True:
        return result(check, "cannot_check", None, threshold,
                      "The strap's actual entry into the seat must be visible and tapped. A point on the front strap cannot show its slot height.")
    p, width, _, v = ref
    delta = float(np.dot(item[1]-p[side+"_shoulder"], v)/width)
    issue = delta < -0.05-1e-9 if seat_type == "rear" else delta > 0.05+1e-9
    target = "at or below" if seat_type == "rear" else "at or above"
    return result(check, "issue" if issue else "looks_right", {"delta": delta}, threshold,
                  f"The tapped entry is {'outside' if issue else 'within'} the unvalidated photo tolerance for {target} shoulder height. Confirm the actual slot using the seat manual.")


def shoulder_belt(keypoints, masks):
    threshold = THRESHOLDS["shoulder_belt"]
    ref, item = references(keypoints), confirmed(masks.get("shoulder_belt"), keypoints)
    if ref is None or item is None:
        return result("shoulder_belt", "cannot_check", None, threshold, "I need a confirmed shoulder-belt mask and clear shoulder/hip points.")
    p, width, u, v = ref
    y, x = np.nonzero(item[0])
    pixels = np.column_stack([x, y])-p["left_shoulder"]
    ratios = pixels@u/width
    near = np.abs(pixels@v/width) <= 0.05
    ratios = ratios[near]
    if not len(ratios) or np.ptp(np.percentile(ratios, [10, 90])) > 0.25:
        return result("shoulder_belt", "cannot_check", None, threshold, "The confirmed mask does not give one narrow shoulder crossing. Retap or check the belt route by hand.")
    ratio = float(np.median(ratios))
    inside = any(low-1e-9 <= ratio <= high+1e-9 for low, high in threshold["accepted_bands"])
    text = "The visible crossing is within the prototype shoulder band." if inside else "The visible crossing may be near the neck or outer arm. Recheck that the belt follows the middle shoulder and chest."
    return result("shoulder_belt", "looks_right" if inside else "issue", {"crossing_ratio": ratio}, threshold,
                  text+" This unvalidated measurement does not verify the full hidden belt route.")


def lap_belt(keypoints, masks):
    threshold = THRESHOLDS["lap_belt"]
    ref, item = references(keypoints), confirmed(masks.get("lap_belt"), keypoints)
    if ref is None or item is None:
        return result("lap_belt", "cannot_check", None, threshold, "I need a confirmed lap-belt mask and clear hip/shoulder points. Hidden belt sections need a manual check.")
    p, width, u, v = ref
    hips = (p["left_hip"]+p["right_hip"])/2
    y, x = np.nonzero(item[0])
    pixels = np.column_stack([x, y])-hips
    extent = sorted([float(np.dot(p[s+"_hip"]-hips, u)/width) for s in ("left", "right")])
    lateral = pixels@u/width
    vertical = pixels@v/width
    values = vertical[(lateral >= extent[0]-0.10) & (lateral <= extent[1]+0.10)]
    if not len(values) or np.ptp(np.percentile(values, [10, 90])) > 0.20:
        return result("lap_belt", "cannot_check", None, threshold, "The mask is too broad or does not show a narrow lap belt by the hips. Retap or check by hand.")
    delta = float(np.median(values))
    inside = -0.05-1e-9 <= delta <= 0.25+1e-9
    text = "The visible lap belt is in the prototype hip/upper-thigh band." if inside else (
        "The visible lap belt may be high on the abdomen." if delta < -0.05 else "The visible lap belt may be too far down the thighs.")
    return result("lap_belt", "looks_right" if inside else "issue", {"delta": delta}, threshold,
                  text+" Thresholds are unvalidated; check that it sits low and snug using the manual.")


def evaluate(keypoints, masks, seat_type):
    if seat_type not in SEATS:
        raise ValueError("Choose rear, forward, or booster.")
    checks = [shoulder_belt(keypoints, masks), lap_belt(keypoints, masks)] if seat_type == "booster" else [
        chest_clip(keypoints, masks), harness_height(keypoints, masks, seat_type, "left"),
        harness_height(keypoints, masks, seat_type, "right")]
    for name, text in MANUAL.items():
        checks.append(result(name, "cannot_check", None, {"photo_measurement": False}, text))
    return checks
