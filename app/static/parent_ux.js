// WHY: change the normal screen layout only; labeling keeps its existing elements and handlers.
function installParentUX(){
    if(labeling)return;
    const reduced=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
    const css=document.createElement('link');css.rel='stylesheet';css.href='/static/native.css';document.head.append(css);
    document.body.classList.add('native-mode');
    document.querySelector('meta[name="viewport"]').content='width=device-width, initial-scale=1, viewport-fit=cover';
    const theme=matchMedia('(prefers-color-scheme: dark)');
    function statusBar(){
        document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]').content=theme.matches?'black-translucent':'default';
        document.querySelector('meta[name="theme-color"]').content=theme.matches?'#101b19':'#f3f7f5';
    }
    statusBar();theme.addEventListener('change',statusBar);
    const paths={
        camera:'<path d="M4 7h4l2-3h4l2 3h4v13H4z"/><circle cx="12" cy="13" r="4"/>',
        belt:'<path d="m5 3 14 18M19 3 5 21M3 15h18"/><rect x="9" y="12" width="6" height="5" rx="1"/>',
        clip:'<path d="M7 3v18M17 3v18"/><rect x="4" y="9" width="16" height="6" rx="2"/>',
        check:'<path d="m5 12 4 4L19 6"/>',
        alert:'<path d="m12 3 10 18H2zM12 9v5m0 3v.1"/>',
        info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
        back:'<path d="m15 5-7 7 7 7"/>',
        close:'<path d="m6 6 12 12M18 6 6 18"/>',
        person:'<circle cx="12" cy="6" r="3"/><path d="M5 21v-4a7 7 0 0 1 14 0v4M8 15h8"/>',
        sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1"/>',
        seat:'<path d="M7 3v10a4 4 0 0 0 4 4h8M5 21h15M8 17l-1 4m10-4 1 4"/><path d="m11 5 3 8h5"/>',
        arrow:'<path d="M5 12h14m-5-5 5 5-5 5"/>'
    };
    function icon(name){return `<svg class="sc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${paths[name]||paths.info}</svg>`;}
    // WHY: make the three seat types easier to recognize without changing what each choice means.
    function seatIllustration(seat){
        const drawings={
            rear:'<path d="M46 15 51 43q2 10-10 16l-23 6q-8 1-6-7l9-9 7-22q5-14 18-12Z"/><circle cx="35" cy="27" r="6"/><path d="m34 34-4 10-10 1-6 9m22-18 4 10-10 6M29 37l8 6M18 70h32M20 10H8m5-5-5 5 5 5"/>',
            forward:'<path d="M15 15 12 46q-1 13 11 16h28q5 0 3-7l-5-6H29l-4-27q-1-9-10-7Z"/><circle cx="30" cy="26" r="6"/><path d="m29 33 3 12h12v12m-15-22-5 10 8 6m-8-15 10 9M14 70h39M43 10h13m-5-5 5 5-5 5"/>',
            booster:'<circle cx="32" cy="19" r="7"/><path d="M20 47V35q12-12 24 0v12M24 33l-7 12m23-12 7 12M25 56v14m14-14v14M18 48h28l4 11H14l4-11ZM47 25 25 49M18 45l28 3"/><rect x="29" y="44" width="7" height="7" rx="1"/>'
        };
        return `<svg class="seat-illustration" viewBox="0 0 64 80" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">${drawings[seat]}</svg>`;
    }
    function element(tag,className='',text=''){const node=document.createElement(tag);node.className=className;node.textContent=text;return node;}
    function button(id,text,svg){const node=element('button','',text);node.id=id;node.type='button';if(svg)node.insertAdjacentHTML('afterbegin',icon(svg));return node;}
    const legacy=document.querySelector('main');legacy.hidden=true;
    const app=element('main','native-app');app.id='nativeApp';
    app.innerHTML=`<header class="app-nav"><button id="navBack" type="button" aria-label="Go back">${icon('back')}</button><span id="navTitle">SeatCheck</span><button id="appInfo" type="button" aria-label="About photo checks and privacy">${icon('info')}</button></header><div id="screenStack"></div><div id="mainActionBar"><button id="mainAction" type="button"></button></div>`;
    document.body.append(app);app.querySelector('.app-nav').after($('message'));
    const screens={};
    function screen(id,title,markup){
        const node=element('section','app-screen');node.id='screen-'+id;node.setAttribute('aria-label',title);node.hidden=true;node.innerHTML=markup;
        $('screenStack').append(node);screens[id]=node;return node;
    }
    screen('home','Welcome',`<div class="screen-content home-content"><div class="home-art"><img src="/static/icon.svg" width="88" height="88" alt=""><span class="orbit orbit-one"></span><span class="orbit orbit-two"></span></div><h1 tabindex="-1">SeatCheck</h1><p class="home-purpose">A closer look at belt and harness fit.</p><div id="homeLimits"></div><div id="homePrivacy"></div></div>`);
    // WHY: keep Home short, but leave the full privacy explanation in Info.
    const privacyDetails=$('privacy').cloneNode(true);privacyDetails.removeAttribute('id');
    const prototypeNote=element('p','','A student-built prototype. Manual checks and certified help still matter.');
    $('privacy').textContent='Processed on your SeatCheck computer, without saving the photo.';
    $('homeLimits').append(document.querySelector('.notice'));$('homePrivacy').append($('privacy'));
    screen('seat','Seat type',`<div class="screen-content"><p class="sc-eyebrow">LET’S GET STARTED</p><h1 tabindex="-1">Which seat?</h1><p class="screen-intro">Choose the seat in your photo.</p><div id="seatChoices" class="seat-choices" role="group" aria-label="Seat type"></div></div>`);
    for(const [value,title,sub] of [['rear','Rear-facing','Harness seat · facing backward'],['forward','Forward-facing','Harness seat · facing forward'],['booster','Booster / seat belt','Vehicle shoulder and lap belt']]){
        const choice=button('seat-'+value,'');choice.className='seat-choice';choice.dataset.seat=value;choice.setAttribute('aria-pressed','false');
        choice.innerHTML=`<span class="seat-art">${seatIllustration(value)}</span><span><strong>${title}</strong><small>${sub}</small></span><span class="selection-mark">${icon('check')}</span>`;
        choice.onclick=()=>{$('seatType').value=value;selected=value;document.querySelectorAll('.seat-choice').forEach(n=>n.setAttribute('aria-pressed',String(n===choice)));syncAction();};$('seatChoices').append(choice);
    }
    screen('photo','Choose a photo',`<div class="screen-content"><p class="sc-eyebrow">ONE CLEAR PHOTO</p><h1 tabindex="-1">Let’s take a look.</h1><p class="screen-intro">Stay parked while taking your photo.</p><div class="camera-art">${icon('camera')}<span>Show the belt or harness</span></div><button id="chooseLibrary" class="secondary" type="button">Choose photo</button><ul class="framing-tips"><li>${icon('person')}<span>One child in the photo.</span></li><li>${icon('belt')}<span>Show both shoulders and hips.</span></li><li>${icon('sun')}<span>Use clear, even light.</span></li></ul></div>`);
    screen('analyze','Body points',`<div id="analyzeStage" class="photo-stage"><div class="scan-line" aria-hidden="true"></div></div><div class="bottom-sheet" id="poseSheet"><div class="sheet-grip" aria-hidden="true"></div><p class="sc-eyebrow" id="poseKicker">FINDING BODY POINTS</p><h2 id="poseQuestion" tabindex="-1">Looking at your photo…</h2><div id="poseCopy"></div><button id="retakePhoto" class="text-button" type="button">Retake</button></div>`);
    screen('tap','Tap and confirm',`<div class="tap-toolbar"><span id="nativeProgress" class="sc-eyebrow"></span><span id="instructionChip" role="heading" aria-level="1" tabindex="-1" aria-live="polite" aria-atomic="true"></span></div><div id="tapStage" class="photo-stage"></div><div class="bottom-sheet" id="itemSheet"><div class="sheet-grip" aria-hidden="true"></div><div id="tapCopy"></div><div id="tapSecondary" class="tap-secondary"></div></div>`);
    screen('results','Photo review',`<div class="screen-content results-content"><p class="sc-eyebrow">YOUR PHOTO REVIEW</p><h1 tabindex="-1">A clearer next step.</h1><p class="screen-intro">Visible items only. Hand checks still matter.</p><div id="resultCounts" class="result-counts" aria-label="Photo review counts"></div><div id="xraySlot"></div><div id="resultList"></div><p class="result-limit">UNVALIDATED photo checks.<br>A photo does not replace an inspection.</p></div>`);
    // WHY: only normal mode loads the drawing code, so labeling keeps its own layout and controls.
    let xrayView=null;
    const xrayReady=import('/static/xray.js').then(module=>{xrayView=module.installXray($('xraySlot'));return xrayView;}).catch(()=>null);
    let xrayResponse=null;const originalAPI=api;
    api=async(path,data)=>{const result=await originalAPI(path,data);if(path==='/api/results')xrayResponse=result;return result;};
    screen('next','Next steps',`<div class="screen-content next-content"><p class="sc-eyebrow">FINISH WITH A HAND CHECK</p><h1 tabindex="-1">Next steps.</h1><p class="screen-intro">Some things need your hands and the seat manual.</p><div id="handCheckSlot"></div><div id="coatSlot"></div><section class="inspection-block"><h2>Get a second look.</h2><p>A certified inspection is the next step.</p><div id="inspectionSlot"></div></section><div id="anotherSlot"></div></div>`);
    const hidden=element('div');hidden.hidden=true;app.append(hidden);
    // WHY: move the existing controls; replacing them would lose their tap and confirmation handlers.
    for(const id of ['photoInput','cameraInput','seatType','poseButton','startTaps','confirmMask','stepPhoto','stepTap','stepResults'])hidden.append($(id));
    $('screen-photo').append($('photoInput'),$('cameraInput'));
    for(const input of [$('photoInput'),$('cameraInput')]){input.setAttribute('aria-hidden','true');input.tabIndex=-1;}
    const photoPanel=$('photoPanel'),frame=element('div','native-photo-frame');frame.id='photoFrame';frame.append(canvas);photoPanel.replaceChildren(frame);$('analyzeStage').append(photoPanel);
    const decoration=document.createElementNS('http://www.w3.org/2000/svg','svg');decoration.id='photoDecoration';decoration.setAttribute('aria-hidden','true');decoration.style.pointerEvents='none';frame.append(decoration);
    $('poseCopy').append($('poseNote'));hidden.append($('posePanel'));
    $('tapCopy').append($('tapHelp'),$('maskQuestion'),$('suggestionNote'),$('useSuggestion'));
    $('tapSecondary').append($('retap'),$('skip'));hidden.append($('tapPanel'));
    $('retap').textContent='Retap';$('skip').textContent="Can’t see it";
    $('resultList').append($('visualCards'));hidden.append($('results'));
    const checklist=element('details');checklist.id='manualChecklist';const summary=element('summary','','Hands-on checks');checklist.append(summary,$('manualCards'));$('handCheckSlot').append(checklist);
    $('coatSlot').append($('coatPanel'));
    $('anotherSlot').append($('newPhoto'));$('newPhoto').textContent='Check another photo';$('newPhoto').hidden=false;
    const dialog=document.createElement('dialog');dialog.id='detailSheet';dialog.className='detail-sheet';dialog.setAttribute('aria-labelledby','detailTitle');
    dialog.innerHTML=`<div class="dialog-heading"><h2 id="detailTitle">Photo check details</h2><button id="closeDetails" type="button" aria-label="Close details">${icon('close')}</button></div><div id="detailContent"></div>`;document.body.append(dialog);
    let current='home',selected=null,poseReady=false,poseFailed=false,transition=null,navigation=0,returnFocus=null,lastCounts='',countAnimation=0;
    const names={home:'SeatCheck',seat:'Seat type',photo:'Photo',analyze:'Body points',tap:'Tap & confirm',results:'Photo review',next:'Next steps'};
    function closeDetails(){dialog.close();if(returnFocus?.isConnected)returnFocus.focus({preventScroll:true});}
    $('closeDetails').onclick=closeDetails;dialog.addEventListener('cancel',event=>{event.preventDefault();closeDetails();});dialog.addEventListener('click',event=>{if(event.target===dialog)closeDetails();});
    dialog.addEventListener('keydown',event=>{
        if(event.key!=='Tab')return;
        // WHY: keep source links in the tab order, even if Safari normally skips them.
        const stops=[...dialog.querySelectorAll('button,a[href],summary,input,select')].filter(node=>!node.disabled&&node.getClientRects().length);
        event.preventDefault();const index=stops.indexOf(document.activeElement),step=event.shiftKey?-1:1;
        stops[(index+step+stops.length)%stops.length]?.focus();
    });
    function details(title,content,opener=document.activeElement){
        returnFocus=opener;$('detailTitle').textContent=title;$('detailContent').replaceChildren(content);dialog.showModal();$('closeDetails').focus({preventScroll:true});
    }
    $('appInfo').onclick=()=>{const info=element('div','prototype-details');for(const node of [document.querySelector('.notice'),privacyDetails,prototypeNote]){const copy=node.cloneNode(true);copy.removeAttribute('id');info.append(copy);}details('About these photo checks',info,$('appInfo'));};
    function fitPhoto(){
        const stage=current==='tap'?$('tapStage'):$('analyzeStage');if(!canvas.width||!canvas.height||!stage.clientHeight)return;
        const scale=Math.min(stage.clientWidth/canvas.width,stage.clientHeight/canvas.height);
        frame.style.width=canvas.width*scale+'px';frame.style.height=canvas.height*scale+'px';
    }
    new ResizeObserver(fitPhoto).observe($('analyzeStage'));new ResizeObserver(fitPhoto).observe($('tapStage'));
    function applyScreen(id,direction){
        current=id;app.dataset.screen=id;app.dataset.direction=direction;
        Object.entries(screens).forEach(([name,node])=>{node.hidden=name!==id;node.inert=name!==id;node.classList.remove('screen-enter');});
        if(id==='analyze'||id==='tap'){(id==='tap'?$('tapStage'):$('analyzeStage')).append(photoPanel);photoPanel.hidden=false;canvas.setAttribute('aria-describedby',id==='tap'?'instructionChip tapHelp':'poseNote');}
        screens[id].classList.add('screen-enter');$('navTitle').textContent=names[id];$('navBack').hidden=id==='home';syncAction();fitPhoto();
        const heading=screens[id].querySelector('h1,h2,[role=heading]');if(heading)heading.focus({preventScroll:true});
    }
    function go(id,direction='forward'){
        const ticket=++navigation;transition?.skipTransition();
        if(current===id){syncAction();fitPhoto();return;}
        document.documentElement.dataset.scDirection=direction;
        const change=()=>{if(ticket===navigation)applyScreen(id,direction);};
        document.documentElement.classList.toggle('sc-view-transitions',!reduced() && !!document.startViewTransition);
        if(!reduced() && document.startViewTransition){transition=document.startViewTransition(change);transition.finished.catch(()=>{});transition.ready.catch(()=>{});}
        else change();
    }
    function syncAction(){
        app.dataset.busy=String(busy);const action=$('mainAction');let label,svg='arrow',disabled=busy;
        if(current==='home')label='Check a seat';
        if(current==='seat'){label='Continue';disabled=busy||!selected;}
        if(current==='photo'){label='Take photo';svg='camera';}
        if(current==='analyze'){label=poseReady?(state.keypoints?.people===1?'Yes, continue':'Continue to taps'):poseFailed?'Choose another photo':'Analyzing photo…';disabled=busy||(!poseReady&&!poseFailed);svg=poseReady?'check':'info';}
        if(current==='tap'){label=busy?'Tracing item…':'Confirm';disabled=busy||$('confirmMask').disabled;svg='check';}
        if(current==='results')label='Next steps';
        if(current==='next'){label='Open the NHTSA locator';svg='arrow';}
        if(action.dataset.label!==label){action.innerHTML=icon(svg)+`<span>${label}</span>`;action.dataset.label=label;}
        action.disabled=disabled;action.setAttribute('aria-label',current==='next'?'Open the NHTSA locator in a new tab':label);$('navBack').disabled=busy;
    }
    $('mainAction').onclick=()=>{
        if(busy)return;
        if(current==='home')go('seat');else if(current==='seat')go('photo');else if(current==='photo')$('cameraInput').click();
        else if(current==='analyze'){if(poseReady)$('startTaps').click();else if(poseFailed)go('photo','back');}else if(current==='tap')$('confirmMask').click();
        else if(current==='results')go('next');else if(current==='next')$('inspectionLink').click();
    };
    $('navBack').onclick=()=>{
        if(busy)return;
        if(current==='results'){state.index=state.tasks.length-1;showTask();return;}
        go({seat:'home',photo:'seat',analyze:'photo',tap:'analyze',next:'results'}[current]||'home','back');
    };
    $('chooseLibrary').onclick=()=>$('photoInput').click();$('retakePhoto').onclick=()=>go('photo','back');
    function poseDecoration(){
        decoration.setAttribute('viewBox',`0 0 ${canvas.width} ${canvas.height}`);decoration.replaceChildren();
        if(!poseReady)return;
        for(const [i,name] of ['left_shoulder','right_shoulder','left_hip','right_hip'].entries()){
            const point=state.keypoints?.points?.[name];if(!point||!Number.isFinite(point.x)||!Number.isFinite(point.y))continue;
            const circle=document.createElementNS(decoration.namespaceURI,'circle');circle.setAttribute('cx',point.x);circle.setAttribute('cy',point.y);circle.setAttribute('r',Math.max(5,canvas.width/55));circle.style.setProperty('--i',i);circle.classList.add('body-dot');decoration.append(circle);
        }
    }
    function maskDecoration(){
        decoration.replaceChildren();const overlay=state.candidate?.overlay;if(!overlay)return;
        // WHY: this outline is just decoration; do not change the strap mask, tap, or request pixels.
        const {width,height}=overlay,pixels=overlay.getContext('2d').getImageData(0,0,width,height).data;let path='';
        const on=(x,y)=>x>=0&&y>=0&&x<width&&y<height&&pixels[(y*width+x)*4+3]>0;
        for(let y=0;y<height;y++)for(let x=0;x<width;x++)if(on(x,y)){
            if(!on(x,y-1))path+=`M${x} ${y}h1`;if(!on(x,y+1))path+=`M${x} ${y+1}h1`;
            if(!on(x-1,y))path+=`M${x} ${y}v1`;if(!on(x+1,y))path+=`M${x+1} ${y}v1`;
        }
        decoration.setAttribute('viewBox',`0 0 ${width} ${height}`);const outline=document.createElementNS(decoration.namespaceURI,'path');outline.setAttribute('d',path);outline.setAttribute('pathLength','1');outline.classList.add('mask-outline');decoration.append(outline);
    }
    const originalBusy=setBusy;setBusy=value=>{originalBusy(value);syncAction();};
    const originalPose=$('poseButton').onclick;$('poseButton').onclick=async()=>{
        poseReady=false;poseFailed=false;app.dataset.poseReady='false';$('poseQuestion').textContent='Looking at your photo…';$('poseKicker').textContent='FINDING BODY POINTS';decoration.replaceChildren();go('analyze');
        await originalPose();poseReady=!$('posePanel').hidden;poseFailed=!poseReady;app.dataset.poseReady=String(poseReady);
        $('poseQuestion').textContent=poseReady?'Do these dots match your child?':'Could not find body points.';
        $('poseKicker').textContent=poseReady?'REVIEW THE ESTIMATES':'TRY ANOTHER PHOTO';$('retakePhoto').hidden=busy;
        poseDecoration();syncAction();fitPhoto();
    };
    for(const input of [$('photoInput'),$('cameraInput')]){
        input.removeEventListener('change',choosePhoto);input.addEventListener('change',async event=>{
            if(!event.target.files[0]||busy)return;const before=state;poseReady=false;poseFailed=false;app.dataset.poseReady='false';$('poseQuestion').textContent='Looking at your photo…';$('poseKicker').textContent='FINDING BODY POINTS';go('analyze');
            await choosePhoto(event);
            if(state!==before && state.stage==='photo')await $('poseButton').onclick();else go('photo','back');
        });
    }
    const originalStart=$('startTaps').onclick;$('startTaps').onclick=()=>{originalStart();go('tap');};
    const originalTask=showTask;showTask=()=>{
        originalTask();$('instructionChip').textContent=$('tapTitle').textContent;$('nativeProgress').textContent=`${state.index+1} of ${state.tasks.length}`;
        decoration.replaceChildren();go('tap');if(current==='tap')$('instructionChip').focus({preventScroll:true});syncAction();
    };
    const originalTrace=traceTap;traceTap=async tap=>{await originalTrace(tap);maskDecoration();syncAction();};
    const originalCard=card;card=check=>{
        const article=originalCard(check);if(check.threshold.photo_measurement===false)return article;
        const open=button('','');open.removeAttribute('id');open.className='result-open';open.setAttribute('aria-haspopup','dialog');open.setAttribute('aria-label',`${titles[check.check]||check.check}: ${check.status.replaceAll('_',' ')}. Open details`);
        const glyph=element('span','result-icon');glyph.innerHTML=icon(check.status==='issue'?'alert':check.status==='looks_right'?'check':'info');
        const copy=element('span','result-copy');for(const node of [...article.children])if(!node.matches('details'))copy.append(node);
        const why=article.querySelector('.why');open.append(glyph,copy);article.prepend(open);article.classList.add('native-result');
        function openDetails(opener){
            const full=originalCard(check),why=full.querySelector('.why');why.open=true;
            // WHY: keep the exact numbers available, but do not make a parent read JSON to understand them.
            for(const paragraph of why.querySelectorAll('p'))if(paragraph.textContent.startsWith('SeatCheck prototype measurement:'))paragraph.remove();
            const sentence=element('p','measurement-copy',measurementCopy(check));why.querySelector('p').after(sentence);
            const technical=element('details','technical-details'),heading=element('summary','','Technical details');
            const raw=element('pre','',JSON.stringify({measured_value:check.measured_value,threshold:check.threshold,
                ...(check.correction?{correction:check.correction}:{}),...(check.quality_gate?{quality_gate:check.quality_gate}:{})},null,2));
            technical.append(heading,raw);why.append(technical);details(titles[check.check]||check.check,full,opener);
        }
        open.onclick=()=>openDetails(open);why.querySelector('summary').onclick=event=>{event.preventDefault();openDetails(event.currentTarget);};return article;
    };
    function counts(){
        const issues=$('visualCards').querySelectorAll('.issue').length,looks=$('visualCards').querySelectorAll('.looks_right').length;
        const hand=$('visualCards').querySelectorAll('.cannot_check').length+$('manualCards').children.length+$('coatReminder').children.length;
        const values=[issues,looks,hand],key=values.join(',');if(key===lastCounts)return;lastCounts=key;cancelAnimationFrame(countAnimation);
        $('resultCounts').replaceChildren();for(const [i,label] of ['issues','looks right','check by hand'].entries()){
            const cell=element('div','count-cell '+['issue','looks_right','cannot_check'][i]);cell.setAttribute('aria-label',`${values[i]} ${label}`);
            const number=element('strong','',String(reduced()?values[i]:0));number.setAttribute('aria-hidden','true');cell.append(number,element('span','',label));$('resultCounts').append(cell);
        }
        if(!reduced()){const start=performance.now();function animate(now){const progress=Math.min(1,(now-start)/450);$('resultCounts').querySelectorAll('strong').forEach((n,i)=>n.textContent=Math.round(values[i]*progress));if(progress<1)countAnimation=requestAnimationFrame(animate);}countAnimation=requestAnimationFrame(animate);}
    }
    const originalRender=renderChecks;renderChecks=records=>{originalRender(records);[...$('visualCards').children].forEach((node,i)=>node.style.setProperty('--i',i));counts();};
    const originalResults=showResults;showResults=async()=>{xrayResponse=null;await originalResults();if(state.stage==='results'){counts();go('results');$('newPhoto').hidden=false;const xray=await xrayReady;xray?.setResult(xrayResponse,state);}};
    const originalNew=$('newPhoto').onclick;$('newPhoto').onclick=()=>{xrayView?.setResult(null,null);xrayResponse=null;originalNew();poseReady=false;lastCounts='';decoration.replaceChildren();$('newPhoto').hidden=false;go('seat','back');};
    new MutationObserver(()=>{syncAction();counts();}).observe($('coatReminder'),{childList:true});
    // WHY: inspection.js loads later; move its link and note here without asking for a ZIP.
    document.addEventListener('DOMContentLoaded',()=>{const link=$('inspectionLink'),note=$('inspectionZipNote');$('inspectionSlot').append(link,note);link.textContent='Open the NHTSA locator ↗';});
    applyScreen('home','forward');
}
installParentUX();
