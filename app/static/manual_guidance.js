// WHY: the parent answers these; the app adds reminders, not an automatic fit verdict.
function coatCheck(answer,seat='rear'){
    if(answer!==true)return null;
    // WHY: a booster uses the car belt, so a harness pinch test is the wrong reminder.
    if(seat==='booster')return {check:'coat_pinch_test',status:'cannot_check',threshold:{photo_measurement:false,validated:false},
        explanation:'Check belt routing by hand using the vehicle manual.',
        guidance:'Keep the lap belt over the upper thighs and the shoulder belt across shoulder and chest.',
        source:'https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats',source_name:'NHTSA',source_section:'Types and Recommendations: Booster Seat / Seat Belt'};
    return {check:'coat_pinch_test',status:'cannot_check',threshold:{photo_measurement:false,validated:false},
        explanation:'Check harness slack by hand using the seat manual.',
        guidance:'Adjust the harness until no extra strap material can be pinched at the shoulder.',
        source:'https://www.nhtsa.gov/car-seats-and-booster-seats/how-install-forward-facing-car-seats',
        source_name:'NHTSA',source_section:'Fitting Your Child Correctly in the Car Seat, step 3'};
}

function readinessCheck(seat){
    if(seat!=='booster')return null;
    return {check:'seat_belt_readiness',status:'cannot_check',threshold:{photo_measurement:false,validated:false},
        explanation:'Review all five belt-fit items by hand with the vehicle manual.',
        checklist:['Back rests against the vehicle seat without slouching.','Knees bend comfortably over the seat edge.',
            'Lap belt sits low and snug across the upper thighs.','Shoulder belt crosses the middle of the chest and shoulder, away from the neck.',
            'Child can stay in that position for the whole trip.'],
        guidance:'Assess seated posture, knee bend, lap and shoulder placement, and the ability to maintain that position throughout the trip.',
        source:'https://www.healthychildren.org/English/safety-prevention/on-the-go/Pages/Seat-Belts-for-Older-Children-Adults.aspx',
        source_name:'AAP HealthyChildren.org',source_section:'Using a Seat Belt: three guidance bullets, arranged as five manual items'};
}

function renderCoatReminder(){
    if(labeling)return;
    const area=$('coatReminder');area.replaceChildren();const check=coatCheck(state.coat,state.seat);
    if(check){titles.coat_pinch_test=state.seat==='booster'?'Coat and belt routing':'Coat and harness slack';area.append(card(check));}
    for(const [id,value] of [['coatYes',true],['coatNo',false]])$(id).setAttribute('aria-pressed',String(state.coat===value));
}

if(!labeling){
    const panel=document.createElement('section');panel.id='coatPanel';panel.className='card';
    const heading=document.createElement('h2');heading.textContent='Wearing a coat?';
    const yes=document.createElement('button'),no=document.createElement('button');
    yes.id='coatYes';no.id='coatNo';yes.textContent='Yes';no.textContent='No';no.className='secondary';
    const reminder=document.createElement('div');reminder.id='coatReminder';
    panel.append(heading,yes,no,reminder);$('visualCards').before(panel);
    // WHY: this answer only changes a hands-on reminder; it does not rerun the photo checks.
    for(const [button,answer] of [[yes,true],[no,false]])button.onclick=()=>{state.coat=answer;renderCoatReminder();};
}
