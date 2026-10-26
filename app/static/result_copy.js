// WHY: turn existing measurements into words without editing the rule or API records.
function resultCopy(check) {
    const value=check.measured_value||{}, limits=check.threshold||{}, name=check.check;
    const delta=value.delta;
    if(check.status!=='issue') return {summary:check.explanation,direction:null};
    let summary=check.explanation,direction=null;
    if(name==='chest_clip' && Number.isFinite(delta) && delta!==0){
        direction=delta>0?'low':'high';
        summary=delta>0?'Chest clip appears too low → slide it up to armpit level.':'Chest clip appears too high → slide it down to armpit level.';
    } else if(name.endsWith('_harness_entry') && Number.isFinite(delta)){
        if(limits.direction==='at_or_below' && delta<0){
            direction='above'; summary='Harness entry appears above the shoulders (rear-facing) → use a lower slot allowed by the seat manual.';
        } else if(limits.direction==='at_or_above' && delta>0){
            direction='below'; summary='Harness entry appears below the shoulders (forward-facing) → use a higher slot allowed by the seat manual.';
        }
    } else if(name==='shoulder_belt' && Number.isFinite(value.crossing_ratio)){
        const bands=limits.accepted_bands, r=value.crossing_ratio;
        if(bands?.length===2 && r>bands[0][1] && r<bands[1][0]){
            direction='neck'; summary='Shoulder belt appears near the neck → move it toward the middle of the collarbone.';
        } else if(bands?.length===2 && (r<bands[0][0] || r>bands[1][1])){
            direction='arm'; summary='Shoulder belt appears near the arm → move it inward toward the middle of the shoulder.';
        }
    } else if(name==='lap_belt' && Number.isFinite(delta) && limits.accepted_band?.length===2){
        if(delta<limits.accepted_band[0]){
            direction='high'; summary='Lap belt appears high on the belly → move it low onto the upper thighs.';
        } else if(delta>limits.accepted_band[1]){
            direction='low'; summary='Lap belt appears too far down the thighs → recheck its position at the hip/upper-thigh crease using the manual.';
        }
    }
    return {summary,direction};
}

// WHY: keep the card short; the full explanation is still under Why.
function briefResult(check) {
    if(check.status==='issue') return resultCopy(check).summary;
    if(['coat_pinch_test','seat_belt_readiness'].includes(check.check))return check.explanation;
    const manual={installation_tightness:'Check belt-path movement by hand using the manual.',pinch_test:'Do the pinch test using the seat manual.',
        recline:'Read the recline indicator and follow the manual.',expiration:'Check the label and manufacturer lifespan guidance.',recalls:'Check model and date with the manufacturer or NHTSA.'};
    if(manual[check.check]) return manual[check.check];
    if(check.status==='looks_right') return {chest_clip:'Chest clip appears near armpit level.',left_harness_entry:'Left entry appears within the photo tolerance; check the slot by hand.',
        right_harness_entry:'Right entry appears within the photo tolerance; check the slot by hand.',shoulder_belt:'The visible shoulder crossing appears within the photo band.',lap_belt:'The visible lap belt appears within the hip/upper-thigh photo band.'}[check.check]||'This visible item appears within the photo tolerance.';
    if(check.quality_gate) return check.explanation.split('. ')[0].replace(/\.$/,'')+'.';
    return {chest_clip:'Show clear body points and confirm the clip center.',left_harness_entry:'Show the actual left strap entry or check it by hand.',
        right_harness_entry:'Show the actual right strap entry or check it by hand.',shoulder_belt:'Confirm a narrow shoulder-belt outline with clear shoulders.',lap_belt:'Confirm a narrow lap-belt outline with clear hips.'}[check.check]||'Check this item by hand using the seat manual.';
}

// WHY: fyi, these are our existing UNVALIDATED numbers, not cutoffs supplied by the source.
function measurementCopy(check) {
    const value=check.measured_value||{}, limits=check.threshold||{}, name=check.check;
    if(limits.photo_measurement===false)return null;
    const number=n=>Math.abs(n).toFixed(2);
    const position=(delta,line)=>delta===0?`at ${line}`:`${number(delta)} shoulder widths ${delta>0?'below':'above'} ${line}`;
    if(Number.isFinite(value.delta)){
        const measured=position(value.delta,name==='chest_clip'?'the estimated armpit line':name==='lap_belt'?'the hip reference':'the shoulder line');
        if(name==='chest_clip' && Number.isFinite(limits.absolute_delta_max))return `Measured: ${measured}; allowed: within ${number(limits.absolute_delta_max)} shoulder widths (UNVALIDATED).`;
        if(name.endsWith('_harness_entry') && Number.isFinite(limits.one_sided_tolerance) && ['at_or_below','at_or_above'].includes(limits.direction))return `Measured: ${measured}; allowed: no more than ${number(limits.one_sided_tolerance)} shoulder widths ${limits.direction==='at_or_below'?'above':'below'} the shoulder line (UNVALIDATED).`;
        if(name==='lap_belt' && limits.accepted_band?.length===2 && limits.accepted_band.every(Number.isFinite)){
            const bound=n=>n===0?'at the reference':`${number(n)} ${n<0?'above':'below'}`;
            return `Measured: ${measured}; allowed: ${bound(limits.accepted_band[0])} to ${bound(limits.accepted_band[1])} in shoulder widths (UNVALIDATED).`;
        }
    }
    if(name==='shoulder_belt' && Number.isFinite(value.crossing_ratio) && limits.accepted_bands?.length===2 && limits.accepted_bands.every(b=>b.length===2&&b.every(Number.isFinite)))return `Measured: crossing at ${value.crossing_ratio.toFixed(2)} of the shoulder span from the L side; allowed: ${limits.accepted_bands.map(b=>b.map(n=>n.toFixed(2)).join('–')).join(' or ')} (UNVALIDATED).`;
    return 'No photo measurement is available; check this item by hand (UNVALIDATED).';
}
