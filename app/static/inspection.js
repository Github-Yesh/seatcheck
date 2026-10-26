// WHY: we could not verify a ZIP link, so let NHTSA ask for it instead of storing it here.
function inspectionURL(){return 'https://www.nhtsa.gov/vehicle-safety/car-seats-and-booster-seats#installation-help-inspection';}
if(!labeling){
    const note=document.createElement('p');
    note.id='inspectionZipNote';note.className='caption';note.textContent='Enter your ZIP there.';
    $('inspectionLink').after(note);
    $('inspectionLink').href=inspectionURL();
}
