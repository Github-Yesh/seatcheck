// WHY: only log time and tap counts when asked; no photos, IDs, coordinates, or browser storage.
if(!labeling && new URLSearchParams(location.search).get('test')==='1'){
    let started=null,taps=0,retaps=0,attempts={};
    window.addEventListener('seatcheck:photo',()=>{started=performance.now();taps=retaps=0;attempts={};});
    window.addEventListener('seatcheck:tap',event=>{const item=event.detail;taps++;if(attempts[item])retaps++;attempts[item]=true;});
    window.addEventListener('seatcheck:results',()=>{
        if(started===null)return;
        const measurement={test_mode:true,milliseconds_to_result:Math.round(performance.now()-started),taps,retaps};started=null;
        api('/api/user-test',measurement).catch(()=>message('Usability timing was not saved; keep using the app or try again.',true));
    });
}
