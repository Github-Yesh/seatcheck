"""Hidden-slot guesses, tested on made-up geometry only. OFF by default, not proof of a slot."""
import numpy as np
from app.core.rules import references,confirmed

CUE_CUTOFFS={'corridor':.20,'max_span':.20,'above':.05,'top':.02,'continuation':.10,'pixels':3,'validated':False}
SLOT_CUTOFFS={'dark':64,'radius':.5,'min_width':.08,'max_width':.30,'max_height':.05,'layout_match':.04,'validated':False}


def strap_cue(points,record,side):
    ref=references(points)
    unknown={'position':'cannot_check','tap':None,'reason':'Visible strap does not establish its hidden entry.'}
    if ref is None or confirmed(record,points) is None:
        return unknown
    mask=record['mask']
    if mask.shape!=(points['height'],points['width']):
        return unknown
    p,width,horizontal,vertical=ref
    shoulder=p[side+'_shoulder']
    y,x=np.nonzero(mask)
    pixels=np.column_stack([x,y])
    offset=pixels-shoulder
    lateral=offset@horizontal/width
    down=offset@vertical/width
    local=np.abs(lateral)<=CUE_CUTOFFS['corridor']
    # WHY: a wide strap mask or one far from the shoulder tells us nothing about a hidden slot.
    if len(pixels)<CUE_CUTOFFS['pixels'] or not local.all() or np.ptp(lateral)>CUE_CUTOFFS['max_span']:
        return unknown
    if np.count_nonzero(down < -CUE_CUTOFFS['above'])>=CUE_CUTOFFS['pixels']:
        index=int(np.argmin(down))
        position='above'
    elif abs(float(down.min()))<=CUE_CUTOFFS['top'] and down.max()>=CUE_CUTOFFS['continuation']:
        index=int(np.argmin(down))
        position='at_or_below'
    else:
        return unknown
    return dict(position=position,tap=[float(v) for v in pixels[index]],reason='UNVALIDATED visible-strap hypothesis; check the slot by hand.')


def slot_candidates(image,points,side):
    import cv2
    ref=references(points)
    if ref is None:
        return []
    p,width,_,_=ref
    shoulder=p[side+'_shoulder']
    gray=cv2.cvtColor(np.asarray(image,dtype=np.uint8),cv2.COLOR_RGB2GRAY)
    _,_,stats,centers=cv2.connectedComponentsWithStats((gray<SLOT_CUTOFFS['dark']).astype(np.uint8))
    candidates=[]
    for (_,_,w,h,_),center in zip(stats[1:],centers[1:]):
        if (SLOT_CUTOFFS['min_width']*width<=w<=SLOT_CUTOFFS['max_width']*width and h<=SLOT_CUTOFFS['max_height']*width and np.linalg.norm(center-shoulder)<=SLOT_CUTOFFS['radius']*width):
            candidates.append(center.tolist())
    return candidates


def slot_cue(image,points,side,layout=None):
    unknown={'position':'cannot_check','tap':None,'reason':'A reviewed complete slot layout is required; empty shapes alone cannot identify a used slot.'}
    if not layout or references(points) is None:
        return unknown
    p,width,_,vertical=references(points)
    known=np.asarray(layout,dtype=float)
    if known.ndim!=2 or known.shape[1]!=2 or len(known)<3 or not np.isfinite(known).all():
        return unknown
    if ((known<0).any() or (known[:,0]>=points['width']).any() or (known[:,1]>=points['height']).any()
            or len(np.unique(known,axis=0))!=len(known)):return unknown
    observed=slot_candidates(image,points,side)
    missing=[point for point in known if not any(np.linalg.norm(point-center)<=SLOT_CUTOFFS['layout_match']*width for center in observed)]
    if len(missing)!=1:
        return unknown
    point=missing[0]
    delta=float((point-p[side+'_shoulder'])@vertical/width)
    if abs(delta)<=CUE_CUTOFFS['top']:
        return unknown
    return dict(position='above' if delta<0 else 'at_or_below',tap=point.tolist(),reason='UNVALIDATED missing-slot hypothesis, not confirmed slot identity.')


def combine_cues(strap,slots):
    # WHY: if the two guesses disagree, or either is missing, we still cannot check the slot.
    if strap['position']=='cannot_check' or strap['position']!=slots['position']:
        return dict(position='cannot_check',tap=None,reason='Strap and empty-slot evidence are missing or disagree; check the slot by hand.')
    return dict(position=slots['position'],tap=slots['tap'],reason='UNVALIDATED agreeing strap/slot hypotheses; verify the actual slot by hand.')
