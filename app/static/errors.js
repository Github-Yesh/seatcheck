// WHY: say what went wrong and what to try next, not a cryptic network error.
function friendlyError(kind){
    return {
        connection:"Cannot reach the computer; keep SeatCheck running and join the same Wi-Fi, then try again.",
        upload:"That photo could not be opened; try a JPEG, PNG or Safari-readable HEIC.",
        no_child:"No child was found; try a brighter photo showing one child’s shoulders and hips.",
        two_people:"More than one person was found; choose a photo showing only the child.",
        busy:"The computer is busy; wait a moment and try again."
    }[kind]||"This photo could not be processed; choose another photo and try again.";
}
