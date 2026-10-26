"""Optional body-only brightness check, OFF by default. Same UNVALIDATED quality gate cutoffs."""
import numpy as np
from app.core.quality import CUTOFFS,landmark_reason,evaluate_photo
from app.core.rules import evaluate,references


def evaluate_body_photo(image,points,masks,seat,enabled=False):
    if not enabled:
        return evaluate_photo(image,points,masks,seat)
    reason=None
    box=None
    if min(image.shape[:2])<CUTOFFS['min_short_edge_px']:
        reason='Photo too small. Use a larger, original photo.'
    reason=reason or landmark_reason(image,points,('shoulders','hips'))
    if not reason and references(points) is None:
        reason='Body points are unclear. Retake a clear photo.'
    if not reason:
        p,width,_,_=references(points)
        body=np.array([p[name] for name in ('left_shoulder','right_shoulder','left_hip','right_hip')])
        margin=max(CUTOFFS['min_context_px'],CUTOFFS['context_shoulder_fraction']*width)
        x0,y0=np.maximum(np.floor(body.min(axis=0)-margin),0).astype(int)
        x1,y1=np.minimum(np.ceil(body.max(axis=0)+margin)+1,[image.shape[1],image.shape[0]]).astype(int)
        box=[int(v) for v in (x0,y0,x1,y1)]
        luma=float(np.mean(image[y0:y1,x0:x1],axis=(0,1))@np.array([.2126,.7152,.0722]))
        if luma<CUTOFFS['min_mean_luma']:
            reason='Photo too dark around the body. Retake it in brighter light.'
    # WHY: look at brightness around the body, but leave the actual model photo alone.
    records=evaluate({} if reason else points,masks,seat)
    for check in records:
        if check['threshold'].get('photo_measurement') is False:
            continue
        needed=('shoulders','hips','elbows') if check['check']=='chest_clip' else ('shoulders','hips')
        blocked=reason or landmark_reason(image,points,needed)
        if blocked:
            check.update(status='cannot_check',measured_value=None,explanation=blocked+' Photo-quality cutoffs are UNVALIDATED.',
                         quality_gate=dict(validated=False,cutoffs=dict(CUTOFFS)))
        check['experiment']=dict(flag='BODY_BRIGHTNESS',validated=False,box=box,margin_shoulder_fraction=CUTOFFS['context_shoulder_fraction'])
        check['explanation']+=' Body-area brightness is UNVALIDATED.'
    return records
