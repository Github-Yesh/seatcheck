// WHY: draw the result we already have; do not send a request or change a measurement or strap mask.
export function installXray(host){
    const node=(tag,cls='',text='')=>{const e=document.createElement(tag);e.className=cls;e.textContent=text;return e;};
    const names={chest_clip:'Chest clip',left_harness_entry:'Left entry',right_harness_entry:'Right entry',shoulder_belt:'Shoulder belt',lap_belt:'Lap belt'};
    const palette={issue:'#ffc46b',looks_right:'#8fe0ae',cannot_check:'#bbc9db'};
    const toggle=node('button','xray-toggle','X-ray view');toggle.id='xrayToggle';toggle.type='button';toggle.disabled=true;
    toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-controls','xrayView');toggle.setAttribute('aria-pressed','false');
    const panel=node('section','xray-view');panel.id='xrayView';panel.hidden=true;panel.setAttribute('aria-label','UNVALIDATED measurement geometry');
    const note=node('p','xray-note','Geometry is UNVALIDATED; dots are model estimates.');
    const frame=node('div','xray-frame'),photo=node('img');photo.alt='Your photo with measurement geometry';
    const masks=node('canvas');masks.setAttribute('aria-hidden','true');
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('aria-hidden','true');
    const legend=node('div','xray-legend');frame.append(photo,masks,svg);panel.append(note,frame,legend);host.append(toggle,panel);
    let result=null,session=null,ticket=0;
    function shape(tag,attrs,parent=svg){const e=document.createElementNS(svg.namespaceURI,tag);for(const [key,value] of Object.entries(attrs))e.setAttribute(key,value);parent.append(e);return e;}
    function line(a,b,cls,color='#c6efff',extra={}){return shape('path',{d:`M${a}L${b}`,class:cls,stroke:color,fill:'none',pathLength:1,...extra});}
    async function draw(){
        const current=++ticket,{geometry,checks}=result,{width:w,height:h}=geometry;
        photo.src=session.image;masks.width=w;masks.height=h;svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.replaceChildren();legend.replaceChildren();
        const context=masks.getContext('2d'),size=w/320*12;
        const text=(point,value,attrs={})=>{const e=shape('text',{x:point[0],y:point[1],class:'xray-label','font-size':size,...attrs});e.textContent=value;return e;};
        const definitions=shape('defs',{});
        for(const [status,color] of Object.entries(palette)){
            const marker=shape('marker',{id:'xray-arrow-'+status,viewBox:'0 0 10 10',refX:8,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'},definitions);
            shape('path',{d:'M0 0 10 5 0 10Z',fill:color},marker);
        }
        // WHY: keep the raw body dots separate from the moved reference lines the checks used.
        const pose=geometry.pose;
        const edges=[['left_shoulder','right_shoulder'],['left_hip','right_hip']];
        for(const side of ['left','right'])for(const [a,b] of [['shoulder','elbow'],['shoulder','hip'],['ear','shoulder']])edges.push([side+'_'+a,side+'_'+b]);
        for(const [a,b] of edges)if(pose[a]&&pose[b])line(pose[a],pose[b],'xray-skeleton xray-line');
        for(const [name,point] of Object.entries(pose)){
            shape('circle',{cx:point[0],cy:point[1],r:size/3,class:'xray-dot'});
            const label=name.replace('left_','L ').replace('right_','R '),left=name.startsWith('left_'),estimate=label.length*size*.54;
            const x=left?Math.max(estimate+4,point[0]-8):Math.min(w-estimate-4,point[0]+8);
            text([x,Math.max(size+3,point[1]-6)],label,{'text-anchor':left?'end':'start'});
        }
        for(const [index,entry] of geometry.measurements.entries()){
            const check=checks.find(c=>c.check===entry.check),record=session.masks[entry.item],color=palette[entry.status]||palette.cannot_check;
            if(record?.confirmed && record.png){
                // WHY: black background pixels are still opaque, so use the existing strap mask decoder.
                const bitmap=await globalThis.overlay(record.png,color).catch(()=>null);
                if(current!==ticket)return;
                if(bitmap)context.drawImage(bitmap,0,0,w,h);
            }
            const reading=node('div','xray-reading');reading.dataset.check=entry.check;
            reading.append(node('h3','',`${index+1} · ${names[entry.check]}`));
            reading.append(node('p','',entry.available?globalThis.measurementCopy(check):'No measurement arrow: '+globalThis.briefResult(check)));
            legend.append(reading);
            if(!entry.available)continue;
            reading.append(node('p','xray-reference',entry.reference.label+' · UNVALIDATED'));
            const ref=entry.reference;line(ref.a,ref.b,'xray-reference-line xray-line');
            for(const zone of entry.zones)line(zone.a,zone.b,'xray-zone',zone.kind==='allowed'?palette.looks_right:palette.issue);
            if(entry.connector)line(...entry.connector,'xray-connector');
            const [from,to]=entry.arrow;
            line(from,to,'xray-measure xray-line',color,{'marker-start':'url(#xray-arrow-'+entry.status+')','marker-end':'url(#xray-arrow-'+entry.status+')'});
            const label=[Math.min(w-12,Math.max(12,from[0]+12)),Math.min(h-12,Math.max(15,from[1]-8))];
            shape('circle',{cx:label[0],cy:label[1]-size/3,r:size*.7,class:'xray-number-dot'});
            text(label,String(index+1),{'text-anchor':'middle'});
        }
        legend.append(node('p','xray-key','Amber = issue · green = looks right · slate = cannot check. Shoulder bands: green = allowed range; amber = neck/arm zones. All geometry is UNVALIDATED.'));
    }
    toggle.onclick=async()=>{
        const open=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-pressed',String(open));panel.hidden=!open;
        if(open && result)await draw();else ticket++;
    };
    return {setResult(response,state){
        // WHY: forget this view's photo and strap masks too when someone starts a new photo.
        ticket++;result=response?.geometry?response:null;session=state;photo.removeAttribute('src');masks.width=masks.height=0;svg.replaceChildren();legend.replaceChildren();
        panel.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-pressed','false');toggle.disabled=!result;
    }};
}
