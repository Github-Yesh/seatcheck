"""Opt-in local timing and tap counts only. No photos, names, or participant IDs."""
import csv
import math
from pathlib import Path
from threading import Lock

FIELDS=('milliseconds_to_result','taps','retaps')
LOCK=Lock()


def validate_record(data):
    if set(data)!=set(FIELDS)|{'test_mode'} or data['test_mode'] is not True:
        raise ValueError('Usability logging requires explicit test mode and numeric fields only.')
    row={name:data[name] for name in FIELDS}
    for name,value in row.items():
        if type(value) not in (int,float) or not math.isfinite(value) or value<0 or value>86_400_000:
            raise ValueError('Invalid usability measurement.')
        if name!='milliseconds_to_result' and (type(value) is not int or value>10_000):
            raise ValueError('Invalid tap count.')
    if row['retaps']>row['taps']:
        raise ValueError('Retries cannot exceed tap attempts.')
    return row


def append_record(data,path):
    row=validate_record(data)
    path=Path(path)
    with LOCK:
        path.parent.mkdir(parents=True,exist_ok=True)
        fresh=not path.exists()
        with path.open('a',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=FIELDS)
            if fresh:
                writer.writeheader()
            writer.writerow(row)
