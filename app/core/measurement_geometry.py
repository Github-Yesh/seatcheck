"""Draw the geometry behind a result we already have. No new fit check happens here."""
import numpy as np

from app.core.experiments import corrected_hips
from app.core.neck_candidate import neck_reference
from app.core.quality import CUTOFFS
from app.core.rules import confirmed, references

ITEMS={'chest_clip':'clip','left_harness_entry':'strap_left','right_harness_entry':'strap_right',
       'shoulder_belt':'shoulder_belt','lap_belt':'lap_belt'}


def geometry_for(points,masks,checks,image_shape):
    """Use the returned measurements and the same reference points, without editing the results."""
    height,width=image_shape[:2]
    out=dict(version=1,validated=False,width=width,height=height,pose={},measurements=[])
    if (points.get('height'),points.get('width'))!=(height,width):
        return out
    if points.get('detected') and points.get('people')==1:
        for side in ('left','right'):
            for joint in ('shoulder','elbow','hip','ear'):
                name=side+'_'+joint
                point=points.get('points',{}).get(name,{})
                value=np.array([point.get('x',np.nan),point.get('y',np.nan),point.get('score',0)],dtype=float)
                if (np.isfinite(value).all() and value[2]>=CUTOFFS['min_landmark_score'] and
                        0<=value[0]<width and 0<=value[1]<height):out['pose'][name]=value[:2].tolist()

    def line(label,origin,axis,span,lo=-.5,hi=.5):
        return dict(label=label,a=(origin+lo*span*axis).tolist(),b=(origin+hi*span*axis).tolist())

    for check in checks:
        name=check['check']
        if name not in ITEMS:
            continue
        item=ITEMS[name]
        mask_record=masks.get(item)
        entry=dict(check=name,item=item,status=check['status'],available=False)
        out['measurements'].append(entry)
        evidence=confirmed(mask_record,points)
        if check['status']=='cannot_check' or check['measured_value'] is None or evidence is None:
            continue
        effective=points
        experiment=check.get('experiment',{})
        flag=experiment.get('flag')
        # WHY: draw the reference the check actually used, not whichever flag the screen seems to show.
        if name=='lap_belt' and flag=='HIP_CORRECTION':
            effective=corrected_hips(points,experiment['candidate'])
        if name=='shoulder_belt' and flag=='NECK_CORRECTION':
            effective=neck_reference(points)
        if effective is None:
            continue
        if item.startswith('strap_') and mask_record.get('entry_visible') is not True:
            continue
        ref=references(effective,('left_elbow','right_elbow') if name=='chest_clip' else ())
        if ref is None:
            continue
        p,span,u,v=ref
        mask,tap=evidence
        value=check['measured_value']
        threshold=check['threshold']
        zones=[]
        connector=None
        if name=='shoulder_belt':
            origin=p['left_shoulder']
            ratio=value['crossing_ratio']
            start=origin+ratio*span*u
            end=origin
            reference=line('Neck reference' if flag=='NECK_CORRECTION' else 'Shoulder reference',origin,u,span,0,1)
            bands=threshold['accepted_bands']
            edges=[0,bands[0][0],bands[0][1],bands[1][0],bands[1][1],1]
            for lo,hi,kind in zip(edges,edges[1:],('arm','allowed','neck','allowed','arm')):
                zones.append(dict(**line(kind,origin,u,span,lo,hi),kind=kind))
            connector=[tap.tolist(),start.tolist()]
        else:
            if name=='chest_clip':
                fraction=threshold['armpit_elbow_fraction']
                armpits=[p[s+'_shoulder']+fraction*(p[s+'_elbow']-p[s+'_shoulder']) for s in ('left','right')]
                origin=np.mean(armpits,axis=0)
                reference=line('Armpit reference',origin,u,span)
            elif name=='lap_belt':
                origin=(p['left_hip']+p['right_hip'])/2
                extent=sorted(float((p[s+'_hip']-origin)@u)/span for s in ('left','right'))
                margin=threshold['hip_margin']
                lo,hi=extent[0]-margin,extent[1]+margin
                reference=line('Corrected hip reference' if flag=='HIP_CORRECTION' else 'Hip reference',origin,u,span,lo,hi)
                # WHY: the lap check measures the strap mask median, so drawing at the tap height could be wrong.
                y,x=np.nonzero(mask)
                lateral=(np.column_stack([x,y])-origin)@u/span
                lateral=lateral[(lateral>=lo)&(lateral<=hi)]
                if not len(lateral):
                    continue
                tap=origin+float(np.median(lateral))*span*u
            else:
                origin=p['left_shoulder' if item=='strap_left' else 'right_shoulder']
                reference=dict(label='Shoulder reference',a=p['left_shoulder'].tolist(),b=p['right_shoulder'].tolist())
            end=origin+float((tap-origin)@u)*u
            start=end+value['delta']*span*v
        entry.update(available=True,reference=reference,arrow=[start.tolist(),end.tolist()],zones=zones)
        if connector is not None:
            entry['connector']=connector
    return out
