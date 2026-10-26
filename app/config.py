"""Normal startup flags live here. Passing all OFF still replays the original v1 checks."""
import json
from pathlib import Path

FLAGS_FILE=Path(__file__).resolve().parents[1]/'data/private/flags.json'
DEFAULT_FLAGS = {'HIP_CORRECTION': False, 'STRAP_ENTRY_CUE': False, 'EMPTY_SLOT_CUE': False, 'POSE_CACHE': False,
                 'BODY_BRIGHTNESS': False, 'MULTI_TAP': False, 'NECK_CORRECTION': False}
# WHY: normal mode uses the requested reference guesses; frozen replay and labels keep raw points.
NORMAL_DEFAULT_FLAGS = {**DEFAULT_FLAGS, 'HIP_CORRECTION': True, 'NECK_CORRECTION': True}


def flags_with(overrides=None):
    result = DEFAULT_FLAGS.copy()
    for name, value in (overrides or {}).items():
        if name not in result or type(value) is not bool:
            raise ValueError('Unknown flag or non-boolean value.')
        result[name] = value
    return result


def load_flags(path=FLAGS_FILE):
    path=Path(path)
    if not path.exists():
        return NORMAL_DEFAULT_FLAGS.copy()
    values=json.loads(path.read_text())
    if not isinstance(values,dict):
        raise ValueError('Flags file must contain a JSON object of boolean flags.')
    return flags_with({**NORMAL_DEFAULT_FLAGS, **values})
