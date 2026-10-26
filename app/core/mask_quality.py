"""Both modes reject obviously body-sized strap masks. These shape checks are UNVALIDATED."""
import numpy as np

from app.core.rules import references

# WHY: these size guesses came from geometry before diagnostics, not from grading photos.
CUTOFFS=dict(max_body_area_fraction=0.75, broad_min_area_fraction=0.20, max_minor_shoulder_fraction=0.50)
ITEMS={'clip','strap_left','strap_right','shoulder_belt','lap_belt'}


def rejection(mask, keypoints, item):
    if item not in ITEMS:
        raise ValueError('Unknown tapped item.')
    ref=references(keypoints)
    reason=None
    if ref is None:
        reason='Cannot judge the outline without clear body points; retake or skip.'
    else:
        p,width,_,vertical=ref
        shoulders=(p['left_shoulder']+p['right_shoulder'])/2
        hips=(p['left_hip']+p['right_hip'])/2
        body_area=width*abs(float((hips-shoulders)@vertical))
        pixels=np.asarray(mask,dtype=bool)
        if pixels.shape!=(keypoints['height'],keypoints['width']) or not pixels.any():
            reason='No usable item outline; retap or skip.'
        else:
            y,x=np.nonzero(pixels)
            points=np.column_stack([x,y]).astype(float)
            area=len(points)/body_area
            # WHY: measure across the strap mask itself; a diagonal belt has a wide box but can still be thin.
            centered=points-points.mean(axis=0)
            _,axes=np.linalg.eigh(centered.T@centered/len(points))
            minor=float(np.ptp(centered@axes[:,0]))/width
            if area>CUTOFFS['max_body_area_fraction']:
                reason='Outline covers too much of the body; retap or skip.'
            elif area>CUTOFFS['broad_min_area_fraction'] and minor>CUTOFFS['max_minor_shoulder_fraction']:
                reason='Outline is too broad for a strap or clip; retap or skip.'
    if reason:
        return dict(rejected=True,reason=reason+' Tip: tap the middle of the strap. Mask-quality cutoffs are UNVALIDATED.',
                    quality_gate=dict(validated=False,cutoffs=dict(CUTOFFS)))
    return None
