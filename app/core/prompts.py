"""Background-point guesses are UNVALIDATED. The first tap stays the measurement point."""
import numpy as np
from app.core.rules import references

ITEMS=('clip','strap_left','strap_right','shoulder_belt','lap_belt')


def refinement_prompts(points,taps,item):
    if item not in ITEMS or not 1<=len(taps)<=3:
        raise ValueError('Use one to three positive points on this item.')
    result=[]
    for tap in taps:
        x,y=float(tap['x']),float(tap['y'])
        if tap.get('label',1)!=1 or not np.isfinite([x,y]).all() or not (0<=x<points['width'] and 0<=y<points['height']):
            raise ValueError('Tap inside the photo with positive points only.')
        result.append(dict(x=x,y=y,label=1))
    ref=references(points)
    if ref is not None:
        p,width,u,v=ref
        shoulders=(p['left_shoulder']+p['right_shoulder'])/2
        hips=(p['left_hip']+p['right_hip'])/2
        center=(shoulders+hips)/2
        positives=np.array([[t['x'],t['y']] for t in result])
        direction=v
        if len(positives)>1 and np.ptp(positives,axis=0).any():
            centered=positives-positives.mean(axis=0)
            _,axes=np.linalg.eigh(centered.T@centered)
            direction=axes[:,-1]
        elif item=='lap_belt':
            direction=u
        elif item=='shoulder_belt':
            left=np.dot(positives[0]-shoulders,u)<=0
            direction=p['right_hip' if left else 'left_hip']-p['left_shoulder' if left else 'right_shoulder']
        normal=np.array([-direction[1],direction[0]])
        normal/=np.linalg.norm(normal)
        if np.dot(center-positives[0],normal)<0:
            normal=-normal

        def background(candidates):
            for point in candidates:
                x,y=point
                relative=point-shoulders
                if not (0<=x<points['width'] and 0<=y<points['height']):
                    continue
                if abs(relative@u)>.5*width or not 0<=relative@v<=(hips-shoulders)@v:
                    continue
                # WHY: do not tell SAM to reject a tap we just told it to include, or repeat a background point.
                if any(np.linalg.norm(point-[t['x'],t['y']])<=.10*width for t in result):
                    continue
                result.append(dict(x=float(x),y=float(y),label=0))
                return

        alternatives=[center+sign*fraction*width*normal for fraction in (.15,.30,.45) for sign in (1,-1)]
        background([center,*alternatives])
        if item!='clip':
            background([positives[0]+sign*fraction*width*normal for fraction in (.15,.30,.45) for sign in (1,-1)])
    return result
