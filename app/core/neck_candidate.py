"""Try an ear/shoulder midpoint as the neck reference. UNVALIDATED; the fit band stays the same."""
from copy import deepcopy
import numpy as np
from app.core.rules import references
from app.core.quality import CUTOFFS


def neck_reference(points):
    ref=references(points)
    if ref is None:
        return None
    p,_,_,vertical=ref
    shifts=[]
    for side in ('left','right'):
        ear=points.get('points',{}).get(side+'_ear',{})
        value=np.array([ear.get('x',np.nan),ear.get('y',np.nan),ear.get('score',0)],dtype=float)
        if not np.isfinite(value).all() or value[2]<CUTOFFS['min_landmark_score'] or not (0<=value[0]<points['width'] and 0<=value[1]<points['height']):
            return None
        shift=float((value[:2]-p[side+'_shoulder'])@vertical)/2
        if shift>=0:
            return None
        shifts.append(shift)
    corrected=deepcopy(points)
    shift=np.mean(shifts)*vertical
    # WHY: move both ends together, like sliding a ruler; the shoulder width unit and fit cutoffs stay put.
    for side in ('left','right'):
        point=corrected['points'][side+'_shoulder']
        point['x']+=float(shift[0])
        point['y']+=float(shift[1])
    return corrected
