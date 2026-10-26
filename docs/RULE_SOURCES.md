# Rule guidance and sources

Opened and checked **2026-10-23**. All guidance below is paraphrased in one sentence per check; no guidance excerpts are quoted. Short section names identify locations. Only opened AAP/NHTSA pages are cited. These are HTML pages, so the locations are section/step names, **not invented PDF page numbers**. No Cosco manual or model-specific page number is asserted.

**Official physical guidance does not validate our photo algorithm.** W means estimated shoulder-to-shoulder pixel distance. All fractions of W, anatomical proxies, confidence gates and ambiguity cutoffs below are **SeatCheck's UNVALIDATED choices**, not numbers supplied by these sources. Manufacturer instructions govern the particular seat. The one-inch installation limit below **is official physical guidance**, not a new photo threshold; the app does not measure it.

## Official guidance (shown by “Why?”)

| Check / result card | One-sentence official guidance | Opened source and exact location |
|---|---|---|
| Chest clip | Position the chest clip level with the child's armpits. | [NHTSA — How to Install Forward-Facing Car Seats](https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-forward-facing-car-seats), “Fitting Your Child Correctly in the Car Seat,” step 4; rear-facing fitting step 4 on [NHTSA's rear-facing page](https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-rear-facing-car-seats) confirms the same height. |
| Harness entry — rear-facing, both sides | Use harness slots level with or lower than the shoulders when rear-facing. | [NHTSA — How to Install Rear-Facing Car Seats](https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-rear-facing-car-seats), “Fitting Your Child Correctly in the Car Seat,” step 2. |
| Harness entry — forward-facing, both sides | For forward-facing, route harness straps through slots at shoulder height or higher. | [NHTSA — How to Install Forward-Facing Car Seats](https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-forward-facing-car-seats), “Fitting Your Child Correctly in the Car Seat,” step 2; follow the stated seat-specific slot instructions. |
| Shoulder belt | Position the shoulder belt across shoulder and chest, away from neck and face. | [NHTSA — Car Seats and Booster Seats](https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats), “Types and Recommendations,” Booster Seat / Seat Belt, ages 8–12. |
| Lap belt | Keep the lap belt snug over the upper thighs, rather than the stomach. | [NHTSA — Car Seats and Booster Seats](https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats), “Types and Recommendations,” Booster Seat / Seat Belt, ages 8–12. |
| Manual: installation tightness | For an installed harness seat, test sideways and fore/aft belt-path movement against the one-inch limit. | [AAP HealthyChildren.org — Car Seats: Information for Families](https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Car-Safety-Seats-Information-for-Families.aspx), “Installation tips for rear-facing car seats,” tight-installation bullet. This concerns an installed harness seat, not a universal attachment test for a loose booster. |
| Manual: harness slack / pinch test | Adjust the harness until no extra strap material can be pinched at the shoulder. | [NHTSA — How to Install Forward-Facing Car Seats](https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-forward-facing-car-seats), “Fitting Your Child Correctly in the Car Seat,” step 3. |
| Manual: recline | Follow the seat's recline instructions and use its angle indicator if provided. | [NHTSA — How to Install Rear-Facing Car Seats](https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-rear-facing-car-seats), “Installing a Car Seat with a Seat Belt,” step 7; its angle-indicator discussion is specifically about rear-facing use. No universal angle or booster recline indicator is asserted. |
| Manual: expiration | Read the manufacture-date label and ask the seat maker about its usable lifespan. | [AAP HealthyChildren.org — Car Seats: Information for Families](https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Car-Safety-Seats-Information-for-Families.aspx), “Shopping for car safety seats” → “Never use a car seat that,” first bullet about seat age. No universal expiration period is asserted. |
| Manual: recalls | Use the seat's model number and manufacture date to check recalls, consulting its maker if recalled. | [NHTSA — Used Car Seat Safety Checklist](https://www.nhtsa.gov/car-seats-and-booster-seats/used-car-seat-safety-checklist), label/model/date and recall bullets. No live recall lookup is performed by the app. |

## SeatCheck implementation — all numerical photo choices UNVALIDATED

Manual coat question (T11): a parent's Yes adds a hands-on harness-slack reminder, not coat detection or an automated verdict; guidance is the existing NHTSA forward-facing fitting step 3 pinch-test sentence above. No coat-thickness/compression claim is inferred from the photo. Labeling mode is unchanged.

This records the **unchanged D13 implementation**, separately from the source statements above. It is not official guidance or a validated conversion to physical units.

| Check | Our numerical computation and limits |
|---|---|
| Chest clip | Armpit proxy = shoulder + 0.25 × (elbow − shoulder), averaged across sides; clip tap's body-vertical offset from that midpoint divided by W must have magnitude ≤0.10. This is neither a detected armpit nor centimeters. |
| Harness entry — rear-facing | For each visible entry, d = body-vertical offset below its shoulder / W; flag an issue for d < −0.05. This 0.05W tolerance is ours, not an official allowance above the shoulder. |
| Harness entry — forward-facing | Same offset; flag an issue for d > +0.05. This 0.05W tolerance is ours, not an official allowance below the shoulder. |
| Shoulder belt | Use mask pixels within 0.05W of the shoulder line; median lateral shoulder ratio must fall in [0.10, 0.30] or [0.70, 0.90]; abstain if the 90th–10th percentile ratio spread exceeds 0.25. These bands do not establish the full chest route. |
| Lap belt | Use pixels within the projected hip span plus 0.10W on each side; median body-vertical offset from hip midpoint / W must fall in [−0.05, 0.25]; abstain if the 90th–10th percentile vertical spread exceeds 0.20W. A photo does not establish snugness. |
| All five manual cards | No numerical photo threshold: always `cannot_check`; the app does not measure movement, feel slack, read a recline indicator/date label or query recalls. Follow the appropriate seat instructions or check by hand. |

Shared **UNVALIDATED measurement gates**: exactly one detected person; required finite, in-image body points with score ≥0.5; nondegenerate shoulder width and torso frame (1e−6 guards); required confirmed, nonempty, correctly sized item mask and an in-mask tap. Harness entries require `entry_visible=True`; hidden/skipped entries abstain. Existing 1e−9 comparison tolerances are arithmetic boundary handling, not official fit allowances. No gate, threshold, status or manual-check logic was changed for this citation task.

## Traceability and gaps

### October 25 additions — opened during T13 official URL verification

- **Manual seat-belt readiness:** check back-against-seat posture, comfortable knee bend, low upper-thigh lap belt, mid-chest/shoulder belt and maintaining that posture for the entire trip. [AAP HealthyChildren.org — Seat Belts for Older Children](https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Seat-Belts-for-Older-Children-Adults.aspx), “Using a Seat Belt,” three bullets. Our UI splits these into five manual items; AAP does not number them as five steps. No automated readiness judgment, age/height estimate or verdict.
- **Coat context:** the [opened AAP family guide](https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Car-Safety-Seats-Information-for-Families.aspx), “Why should I dress my child in thinner layers,” explains bulky clothing can compress and advises thinner layers with a covering over the buckled harness. The current UI keeps the narrower already-cited manual pinch reminder for harnesses and belt-route reminder for boosters; it does not detect clothing.
- **Inspection:** [NHTSA's opened inspection section](https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats#installation-help-inspection) offers certified inspection, free in most cases. Enter ZIP on that locator and check station availability/cost; no supported ZIP URL parameter was verified. Direct script fetch returned 403, while the official page/Inspection link opened through the browsing tool. No ZIP is stored or sent to SeatCheck.

`app/core/rules.py` contains `OFFICIAL_SOURCES` and `RULE_SOURCES`; result metadata carries the guidance, publisher, URL and section even for `cannot_check` and manual cards. Both harness sides select the appropriate rear/forward citation from their existing direction metadata. Tests check documentation parity and preserve a pre-change fingerprint of D13 calculations/constants.

All ten requested guidance entries have opened sources; **no current entry needs an invented citation**. An unmapped future check must display **NEEDS SOURCE**, with no guessed URL. These general sources do not certify the app, approve the shoulder-width thresholds, establish mask/pose correctness or replace the specific seat/vehicle manuals and an in-person inspection.
