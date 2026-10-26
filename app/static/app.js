const $ = id => document.getElementById(id);
const labeling = new URLSearchParams(location.search).get('label') === '1';
let state = {}, busy = false, multiTap = false;
const canvas = $('photo'), ctx = canvas.getContext('2d');
const colors = {clip:'#ed7c48',strap_left:'#3fbfc7',strap_right:'#f2bc51',shoulder_belt:'#3fbfc7',lap_belt:'#f2bc51'};
const tasksFor = seat => seat === 'booster' ? [
    {id:'shoulder_belt',title:'Tap the shoulder belt',help:'Tap a visible part of the diagonal belt across the chest. Confirm only a highlight that follows the belt.'},
    {id:'lap_belt',title:'Tap the lap belt',help:'Tap the belt across the hips, not a hand or clothing. If it is hidden, skip.'}
] : [
    {id:'clip',title:'Tap the center of the chest clip',help:'Tap the clip itself, not the lower crotch buckle. Skip if there is no chest clip or it is hidden.'},
    {id:'strap_left',title:'Tap the strap entry by the L dot',help:'Tap the visible point where the shoulder strap comes out of the seat. A point lower on the front strap cannot show the entry height. Skip if hidden.'},
    {id:'strap_right',title:'Tap the strap entry by the R dot',help:'Tap the other visible strap entry into the seat. Skip if you cannot see where it emerges.'}
];
if (labeling) {
    document.body.classList.add('label-mode');
    $('privacy').textContent = 'Labeling mode: your photo goes to this computer. Nothing is saved until you record consent and choose Save labeling session.';
}
function message(text, error=false) { $('message').textContent=text; $('message').classList.toggle('error',error); }
function syncPromptLayout(){
    if(!labeling)return;
    document.body.classList.toggle('multi-tap',multiTap);const actions=document.querySelector('.actions');
    // WHY: put extra-tap controls under the photo in both modes; OFF keeps the original labeling layout.
    if(multiTap)canvas.after(actions);else $('tapPanel').append(actions);
}
function setBusy(value) {
    busy=value;
    document.querySelectorAll('button,input,select').forEach(el => el.disabled=value);
    if (!value) { $('poseButton').disabled=!state.image; $('confirmMask').disabled=!state.candidate; }
}
async function api(path, data) {
    let response;
    try{response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data),cache:'no-store'});}
    catch(error){throw new Error(labeling?error.message:friendlyError('connection'));}
    if(!labeling && (response.status===429 || response.status>=500))throw new Error(friendlyError('busy'));
    let result;
    try{result=await response.json();}catch(error){throw new Error(labeling?error.message:friendlyError('upload'));}
    if (!response.ok) throw new Error(result.error || 'The photo could not be processed. Please try again.');
    return result;
}
function loadImage(src) { return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('This browser could not open the photo. Try Safari for HEIC, or export a JPEG or PNG.'));image.src=src;}); }
async function overlay(src,color) {
    const image=await loadImage(src), out=document.createElement('canvas');out.width=image.width;out.height=image.height;
    const c=out.getContext('2d');c.drawImage(image,0,0);const pixels=c.getImageData(0,0,out.width,out.height);
    const rgb=color.match(/\w\w/g).map(n=>parseInt(n,16));
    // WHY: use the PNG midpoint to find the strap mask, not little color differences from the canvas.
    for(let i=0;i<pixels.data.length;i+=4){const on=pixels.data[i]>=128;pixels.data[i]=rgb[0];pixels.data[i+1]=rgb[1];pixels.data[i+2]=rgb[2];pixels.data[i+3]=on?105:0;}
    c.putImageData(pixels,0,0);return out;
}
function draw() {
    if(!state.bitmap) return;ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(state.bitmap,0,0);
    const shown=state.candidate?[state.candidate]:state.stage==='results'?Object.values(state.masks):[];
    shown.forEach(item=>{ctx.drawImage(item.overlay,0,0);ctx.fillStyle=colors[item.id];ctx.beginPath();ctx.arc(item.tap[0],item.tap[1],Math.max(6,canvas.width/100),0,Math.PI*2);ctx.fill();});
    if(multiTap && state.stage==='taps')for(const point of state.promptTaps||[]){ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(point[0],point[1],Math.max(4,canvas.width/160),0,Math.PI*2);ctx.fill();}
    const proposal=state.stage==='taps'&&!state.candidate?state.suggestions?.[state.tasks[state.index].id]:null;
    if(proposal){ctx.strokeStyle='#fff';ctx.lineWidth=Math.max(2,canvas.width/300);ctx.beginPath();ctx.arc(proposal.x,proposal.y,Math.max(8,canvas.width/70),0,Math.PI*2);ctx.stroke();}
    const points=state.keypoints?.points||{};ctx.font=`bold ${Math.max(16,canvas.width/30)}px system-ui`;
    ['left_shoulder','right_shoulder','left_hip','right_hip'].forEach((name,index)=>{const p=points[name];if(!p)return;ctx.fillStyle=p.score>=.5?'#fff59a':'#ffac86';ctx.beginPath();ctx.arc(p.x,p.y,Math.max(4,canvas.width/160),0,Math.PI*2);ctx.fill();if(index<2){ctx.strokeStyle='#183b35';ctx.lineWidth=3;ctx.strokeText(index===0?'L':'R',p.x+8,p.y-8);ctx.fillText(index===0?'L':'R',p.x+8,p.y-8);}});
}
async function choosePhoto(event) {
    const file=event.target.files[0];if(!file||busy)return;
    if(!labeling)window.dispatchEvent(new Event('seatcheck:photo'));
    setBusy(true);message('Opening photo…');
    try {
        const url=URL.createObjectURL(file);let image;try{image=await loadImage(url);}finally{URL.revokeObjectURL(url);}
        // WHY: shrink the photo first so taps, body points, and the strap mask all use the same pixel grid.
        const scale=Math.min(1,1280/Math.max(image.width,image.height));canvas.width=Math.round(image.width*scale);canvas.height=Math.round(image.height*scale);
        ctx.drawImage(image,0,0,canvas.width,canvas.height);const data=canvas.toDataURL('image/jpeg',.92);
        state={image:data,bitmap:await loadImage(data),masks:{},candidate:null,stage:'photo'};
        ['posePanel','tapPanel','results','labelPanel'].forEach(id=>$(id).hidden=true);$('setup').hidden=false;$('photoPanel').hidden=false;$('newPhoto').hidden=false;
        ['stepPhoto','stepTap','stepResults'].forEach(id=>$(id).classList.toggle('active',id==='stepPhoto'));
        $('saveStatus').textContent='';draw();message('Photo ready. Choose its seat type, then find body points.');
    } catch(error){message(labeling?error.message:friendlyError('upload'),true);}finally{setBusy(false);event.target.value='';}
}
$('photoInput').addEventListener('change',choosePhoto);$('cameraInput').addEventListener('change',choosePhoto);
$('poseButton').onclick=async()=>{
    setBusy(true);message('Finding body points. The first run may take longer while models load…');
    try{state.seat=$('seatType').value;const result=await api('/api/pose',{image:state.image,...(!labeling?{reuse_pose:true}:{})});multiTap=result.features?.multi_tap===true;syncPromptLayout();state.keypoints=result.keypoints;state.suggestions=result.suggestions||{};draw();$('setup').hidden=true;$('posePanel').hidden=false;
        $('poseNote').textContent=result.keypoints.people===1?'The shoulder and hip dots should belong to the child. If they do not, choose another photo.': 'The model did not find exactly one person. Use a clearer photo of one child; measurements will be marked unavailable for this photo.';
        if(!labeling && result.keypoints.people!==1)$('poseNote').textContent=friendlyError(result.keypoints.people>1?'two_people':'no_child');
        message('Body points ready. Check that they match the child.');
        if(!labeling && result.keypoints.people!==1)message($('poseNote').textContent,true);
    }catch(error){message(error.message,true);}finally{setBusy(false);}
};
function showTask(){
    state.candidate=null;state.promptTaps=[];state.stage='taps';const task=state.tasks[state.index];$('tapTitle').textContent=task.title;$('tapHelp').textContent=task.help;
    const proposal=state.suggestions?.[task.id];$('useSuggestion').hidden=!proposal;$('suggestionNote').hidden=!proposal;
    $('suggestionNote').textContent=proposal?`Proposed point shown by the white ring (model score ${proposal.confidence.toFixed(2)}, not a probability). Use it or tap elsewhere, then review the outline. Skip hidden strap entries.`:'';
    $('tapCount').textContent=`ITEM ${state.index+1} OF ${state.tasks.length}`;$('maskQuestion').hidden=true;$('retap').hidden=true;$('confirmMask').disabled=true;draw();message(labeling?`${task.title}. ${task.help}`:task.title+'.');
    if(!labeling){$('tapHelp').textContent={clip:'Tap the clip center, not the lower buckle.',strap_left:'Tap the visible slot where the left strap enters the seat.',strap_right:'Tap the visible slot where the right strap enters the seat.',shoulder_belt:'Tap the diagonal belt crossing the chest.',lap_belt:'Tap the lap belt across the upper thighs.'}[task.id];}
    if(multiTap)$('tapHelp').textContent='First tap the requested point, then add up to 2 points along this item (UNVALIDATED); Retap starts over.';
}
$('startTaps').onclick=()=>{state.tasks=tasksFor(state.seat);state.index=0;$('posePanel').hidden=true;$('tapPanel').hidden=false;$('stepPhoto').classList.remove('active');$('stepTap').classList.add('active');showTask();};
canvas.onclick=async event=>{
    if(busy||state.stage!=='taps')return;const bounds=canvas.getBoundingClientRect();
    const tap=[(event.clientX-bounds.left)*canvas.width/bounds.width,(event.clientY-bounds.top)*canvas.height/bounds.height];
    await traceTap(tap);
};
async function traceTap(tap){
    if(busy||state.stage!=='taps')return;const task=state.tasks[state.index];
    if(multiTap && (state.promptTaps||[]).length>=3){message('Three points used; confirm the outline or Retap to start over.');return;}
    const prompts=multiTap?[...(state.promptTaps||[]),tap]:[tap];
    if(multiTap)state.promptTaps=prompts;
    if(!labeling)window.dispatchEvent(new CustomEvent('seatcheck:tap',{detail:task.id}));
    setBusy(true);message('Tracing the item you tapped…');
    // WHY: labeling needs the same strap mask picker, even when extra taps are OFF.
    try{const result=await api('/api/segment',{image:state.image,item_type:task.id,taps:prompts.map(p=>({x:p[0],y:p[1],label:1})),...(!labeling?{reuse_pose:true}:{})});
        if(result.rejected){state.candidate=null;draw();$('maskQuestion').hidden=true;$('retap').hidden=false;message(result.reason,true);return;}
        state.candidate={id:task.id,png:result.mask,tap:prompts[0],overlay:await overlay(result.mask,colors[task.id]),confirmed:false,entry_visible:task.id.startsWith('strap_')};
        draw();if(!labeling||multiTap)$('maskQuestion').textContent='Does the outline follow only this item?';$('maskQuestion').hidden=false;$('retap').hidden=false;message(multiTap?`Review the outline (${prompts.length}/3 points); add a point, confirm, retap, or skip.`:'Review the highlight. Confirm it, retap, or skip.');
    }catch(error){if(multiTap){state.candidate=null;draw();}message(error.message,true);}finally{setBusy(false);}
}
$('useSuggestion').onclick=async()=>{const proposal=state.suggestions?.[state.tasks[state.index].id];if(proposal)await traceTap([proposal.x,proposal.y]);};
$('retap').onclick=()=>{showTask();message('Tap the requested item again.');};
function payload(){const masks={};Object.entries(state.masks).forEach(([name,m])=>masks[name]={png:m.png,tap:m.tap,confirmed:m.confirmed,entry_visible:m.entry_visible});return{image:state.image,seat_type:state.seat,masks,...(!labeling?{reuse_pose:true}:{label_mode:true})};}
async function nextTask(){if(++state.index<state.tasks.length){showTask();return;}
    await showResults();}
$('confirmMask').onclick=()=>{if(!state.candidate)return;state.candidate.confirmed=true;state.masks[state.candidate.id]=state.candidate;nextTask();};
$('skip').onclick=()=>{delete state.masks[state.tasks[state.index].id];nextTask();};
const titles={chest_clip:'Chest clip height',left_harness_entry:'Left harness entry',right_harness_entry:'Right harness entry',shoulder_belt:'Shoulder belt crossing',lap_belt:'Lap belt height',installation_tightness:'Installation tightness',pinch_test:'Harness slack / pinch test',recline:'Seat recline',expiration:'Seat expiration',recalls:'Recall status'};
function card(check){const article=document.createElement('article');article.className=`card result-card ${check.status}`;
    const badge=document.createElement('span');badge.className='status';badge.textContent={issue:'ISSUE TO RECHECK',looks_right:'LOOKS RIGHT · PHOTO CHECK',cannot_check:'CANNOT VERIFY'}[check.status];
    const title=document.createElement('h3');title.textContent=titles[check.check]||check.check;const explanation=document.createElement('p');explanation.textContent=labeling?check.explanation:briefResult(check);
    if(!labeling && check.status==='issue'){const direction=resultCopy(check).direction;if(direction)article.dataset.direction=direction;}
    article.append(badge,title,explanation);
    if(!labeling && check.checklist){const list=document.createElement('ul');check.checklist.forEach(text=>{const item=document.createElement('li');item.textContent=text;list.append(item);});article.append(list);}
    if(!labeling && check.threshold.photo_measurement!==false){const note=document.createElement('small');note.className='unvalidated';note.textContent=check.correction?.label||'UNVALIDATED photo check';article.append(note);}
    // WHY: a missing measurement should not hide the official guidance from the parent.
    const why=document.createElement('details'),whyLink=document.createElement('summary');why.className='why';whyLink.textContent='Why?';
    whyLink.setAttribute('aria-label',`Why? ${title.textContent}`);why.append(whyLink);
    if(!labeling){const original=document.createElement('p');original.textContent=check.explanation;why.append(original);}
    const guidance=document.createElement('p');guidance.textContent=`Official guidance: ${check.guidance||'NEEDS SOURCE'}`;why.append(guidance);
    if(check.guidance&&check.source&&check.source_name){const source=document.createElement('a');source.href=check.source;source.target='_blank';source.rel='noopener noreferrer';source.textContent=check.source_name;why.append(source);
        const location=document.createElement('p');location.textContent=check.source_section||'';why.append(location);}
    else{const missing=document.createElement('p');missing.textContent='NEEDS SOURCE';why.append(missing);}
    if(check.threshold.photo_measurement!==false){const note=document.createElement('p');note.textContent="SeatCheck's numeric photo thresholds are UNVALIDATED, not values from this source.";why.append(note);}
    article.append(why);
    if(check.measured_value){const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='SeatCheck measurement · UNVALIDATED';
        const text=document.createElement('p');text.textContent=`SeatCheck prototype measurement: ${JSON.stringify(check.measured_value)}. Our UNVALIDATED threshold: ${JSON.stringify(check.threshold)}. These numbers are not specified by the official source.`;
        details.append(summary,text);if(labeling)article.append(details);else why.append(text);}
    return article;
}
function renderChecks(records){
    // WHY: show issues first without rearranging the result records or the labeling order.
    const order={issue:0,looks_right:1,cannot_check:2};
    const ordered=labeling?records:[...records].sort((a,b)=>order[a.status]-order[b.status]);
    ordered.forEach(c=>$(c.threshold.photo_measurement===false?'manualCards':'visualCards').append(card(c)));
    if(!labeling)renderCoatReminder();
    if(!labeling){const readiness=readinessCheck(state.seat);if(readiness){titles.seat_belt_readiness='Seat-belt readiness · manual only';$('manualCards').append(card(readiness));}
        const summary=$('manualChecklist')?.querySelector('summary');if(summary)summary.textContent=`${$('manualCards').children.length} hands-on checks`;}
}
async function showResults(){setBusy(true);message('Measuring the confirmed items…');
    // WHY: only send confirmed strap masks; skipping an item does not mean it looks right.
    try{const result=await api('/api/results',payload());state.stage='results';state.candidate=null;$('tapPanel').hidden=true;$('results').hidden=false;$('visualCards').replaceChildren();$('manualCards').replaceChildren();
        renderChecks(result.checks);
        if(!labeling)window.dispatchEvent(new Event('seatcheck:results'));
        $('resultTitle').textContent=result.checks.some(c=>c.status==='issue')?'Items to recheck':'Review this photo';$('labelPanel').hidden=!labeling;$('stepTap').classList.remove('active');$('stepResults').classList.add('active');draw();message('Results ready. Review the manual checks too.');$('results').scrollIntoView({behavior:'smooth',block:'start'});
    }catch(error){state.index=state.tasks.length-1;$('tapPanel').hidden=false;showTask();message(error.message,true);}finally{setBusy(false);}
}
$('labelForm').onsubmit=async event=>{event.preventDefault();if(!labeling||busy)return;const metadata=Object.fromEntries(new FormData($('labelForm')));metadata.consent=$('consent').checked?'Y':'N';setBusy(true);$('saveStatus').textContent='Saving locally…';message('Saving this consented labeling session locally…');
    try{const result=await api('/api/label',{...payload(),label_mode:true,metadata});const receipt=`Saved #${result.count} (${metadata.car_id}, ${metadata.deliberate_mistake}, ${metadata.split})`;$('saveStatus').textContent=receipt;message(receipt);}
    catch(error){$('saveStatus').textContent=error.message;message(error.message,true);}finally{setBusy(false);}
};
$('newPhoto').onclick=()=>{state={};canvas.width=canvas.height=0;['photoPanel','posePanel','tapPanel','results','labelPanel','newPhoto'].forEach(id=>$(id).hidden=true);$('setup').hidden=false;$('poseButton').disabled=true;$('stepResults').classList.remove('active');$('stepTap').classList.remove('active');$('stepPhoto').classList.add('active');message('Choose another photo.');window.scrollTo({top:0,behavior:'smooth'});};
