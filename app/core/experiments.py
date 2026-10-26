"""Optional geometry guesses. They are UNVALIDATED; the original rules and quality gate stay put."""
from copy import deepcopy
import numpy as np
from app.config import flags_with
from app.core.quality import evaluate_photo
from app.core.body_quality import evaluate_body_photo
from app.core.rules import references

HIP_CANDIDATES = ('anatomy_torso_fraction', 'shoulder_fraction', 'torso_fraction')
HIP_TORSO_FRACTION = 0.25  # UNVALIDATED quarter-torso guess, written down first in D64.
CORRECTION_LABEL = 'anatomy-based correction, UNVALIDATED'


def corrected_hips(points, candidate=HIP_CANDIDATES[0]):
    if candidate not in HIP_CANDIDATES: raise ValueError('Unknown hip candidate.')
    result=deepcopy(points); ref=references(points)
    if ref is None: return result
    p,width,_,vertical=ref
    torso=np.linalg.norm((p['left_hip']+p['right_hip']-p['left_shoulder']-p['right_shoulder'])/2)
    shift=.10*(width if candidate=='shoulder_fraction' else torso)*vertical
    shoulder_midpoint=(p['left_shoulder']+p['right_shoulder'])/2
    for side in ('left','right'):
        if candidate=='anatomy_torso_fraction':
            # WHY: move the hip guess up toward the shoulders, not sideways; the thigh error is an assumption.
            shift=HIP_TORSO_FRACTION*float((p[side+'_hip']-shoulder_midpoint)@vertical)*vertical
        point=result['points'][side+'_hip']; point['x']-=float(shift[0]);point['y']-=float(shift[1])
    return result


def evaluate_with_flags(image, points, masks, seat, flags=None, hip_candidate=HIP_CANDIDATES[0], slot_layouts=None):
    # WHY: the server passes its flags; leaving them out replays the original v1 checks.
    enabled=flags_with(flags)
    # WHY: all OFF means the original path, with the same inputs and result fields.
    def photo_check(keypoints,records):
        return evaluate_body_photo(image,keypoints,records,seat,enabled['BODY_BRIGHTNESS'])
    records=photo_check(points,masks)
    if enabled['HIP_CORRECTION'] and seat=='booster':
        alternative=photo_check(corrected_hips(points,hip_candidate),masks)
        for index,record in enumerate(records):
            if record['check']=='lap_belt':
                # WHY: moving a hip dot cannot make a dark photo or missing body points usable.
                records[index]=record if 'quality_gate' in record else next(r for r in alternative if r['check']=='lap_belt')
                records[index]['experiment']={'flag':'HIP_CORRECTION','candidate':hip_candidate,'validated':False}
                records[index]['correction']={'label':CORRECTION_LABEL,'validated':False,'candidate':hip_candidate,
                    'fraction':HIP_TORSO_FRACTION if hip_candidate=='anatomy_torso_fraction' else .10,
                    'method':'hip toward shoulder line by fraction of perpendicular torso distance' if hip_candidate=='anatomy_torso_fraction' else hip_candidate}
                records[index]['explanation']+=' '+CORRECTION_LABEL+'.'
    if enabled['NECK_CORRECTION'] and seat=='booster':
        from app.core.neck_candidate import neck_reference
        corrected=neck_reference(points)
        for index,record in enumerate(records):
            if record['check']!='shoulder_belt':
                continue
            if 'quality_gate' in record:
                replacement=deepcopy(record)
            elif corrected is None:
                replacement=deepcopy(record)
                replacement.update(status='cannot_check',measured_value=None,
                    explanation='Ears are unclear or outside the photo; check the shoulder belt by hand.')
            else:
                replacement=next(r for r in photo_check(corrected,masks) if r['check']=='shoulder_belt')
            replacement['explanation']+=' '+CORRECTION_LABEL+'.'
            replacement['correction']=dict(label=CORRECTION_LABEL,validated=False,method='mean ear/shoulder midpoint line',fraction=.5)
            replacement['experiment']=dict(flag='NECK_CORRECTION',validated=False,method='mean ear/shoulder midpoint line')
            records[index]=replacement
    if (enabled['STRAP_ENTRY_CUE'] or enabled['EMPTY_SLOT_CUE']) and seat in ('rear','forward'):
        from app.core.entry_cues import strap_cue,CUE_CUTOFFS,slot_cue,combine_cues,SLOT_CUTOFFS
        for side in ('left','right'):
            record=masks.get('strap_'+side)
            if not record or record.get('entry_visible') is True:
                continue
            cue=strap_cue(points,record,side)
            name=side+'_harness_entry'
            if enabled['EMPTY_SLOT_CUE']:
                cue=combine_cues(cue,slot_cue(image,points,side,(slot_layouts or {}).get(side)))
            if cue['position']!='cannot_check':
                # WHY: this guessed slot point is just for the experiment, not a saved label.
                temporary={**masks,'strap_'+side:{**record,'tap':cue['tap'],'entry_visible':True}}
                replacement=next(r for r in photo_check(points,temporary) if r['check']==name)
            else:
                replacement=next(r for r in records if r['check']==name)
            replacement['experiment']=dict(flag='EMPTY_SLOT_CUE' if enabled['EMPTY_SLOT_CUE'] else 'STRAP_ENTRY_CUE',cue=cue['position'],cutoffs={'strap':CUE_CUTOFFS,'slots':SLOT_CUTOFFS} if enabled['EMPTY_SLOT_CUE'] else CUE_CUTOFFS,validated=False)
            replacement['explanation']+=' '+cue['reason']+' UNVALIDATED entry cue.'
            records=[replacement if r['check']==name else r for r in records]
    return records
