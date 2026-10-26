"""Check suggested taps on separate validation cars, not the test split."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

BAR = dict(hit_rate=.90, minimum_targets=20, minimum_photos=6, validated=False)


def eligible(hits, total, photos):
    return (all(type(v) is int for v in (hits,total,photos)) and 0 <= hits <= total
            and total >= BAR['minimum_targets'] and photos >= BAR['minimum_photos'] and hits/total >= BAR['hit_rate'])


def receipt_ok(checkpoint):
    path = Path(checkpoint)
    try:
        report = json.loads((path.parent/'suggestion_eligibility.json').read_text())
        return (report['bar'] == BAR and report['checkpoint_sha256'] == sha256(path.read_bytes()).hexdigest()
                and report['eligible'] is True and eligible(report['hits'], report['total'], report['photos']))
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError):
        return False


def validate(run, graphics):
    from PIL import Image, ImageDraw, ImageFilter
    from train.dataset import targets
    from train.model import load_checkpoint, predict, NAMES
    run, graphics = Path(run), Path(graphics)
    model, data = load_checkpoint(run/'best.pt')
    manifest = data['manifest']
    validation = manifest['splits']['val']
    train_cars = set(manifest['car_groups']['train'])
    validation_cars=set(manifest['car_groups']['val'])
    test_cars=set(manifest['car_groups']['test'])
    if validation_cars & (train_cars|test_cars):
        raise ValueError('Validation cars overlap another split.')
    hits = total = photos = 0
    overlays = []
    for path in validation:
        annotation=Path(path)
        saved=json.loads(annotation.read_text())
        meta=saved['info']['metadata']
        # WHY: check the split first, before targets() can open any photo or strap mask.
        if meta['split'] != 'train' or meta['car_id'] not in validation_cars:
            raise ValueError('Eligibility requires car-disjoint TRAIN validation, never TEST.')
        frozen=manifest['files'][str(path)]
        photo_path=annotation.parent/saved['images'][0]['file_name']
        if (sha256(annotation.read_bytes()).hexdigest()!=frozen['annotations_sha256']
                or sha256(photo_path.read_bytes()).hexdigest()!=frozen['image_sha256']):
            raise ValueError('TRAIN validation data changed after checkpoint selection.')
        photo, _, visible, _, masks = targets(path)
        if not visible.any():
            continue
        photos += 1
        with Image.open(photo) as image:
            image = image.convert('RGB')
            predictions = predict(model, image, data['input_size'], data['label_counts'])
            # WHY: blur the whole photo instead of hoping a face detector finds every face.
            overlay = image.resize((24,24)).resize(image.size).filter(ImageFilter.GaussianBlur(max(image.size)/12))
            draw = ImageDraw.Draw(overlay)
            for index, name in enumerate(NAMES):
                if not visible[index]:
                    continue
                total += 1
                guess = predictions.get(name)
                if guess:
                    x,y = guess['x'],guess['y']
                    mask=masks[name]['mask']
                    hit = 0 <= x < mask.shape[1] and 0 <= y < mask.shape[0] and mask[int(y),int(x)]
                    hits += int(hit)
                    draw.ellipse((x-5,y-5,x+5,y+5),fill='#28a699' if hit else '#e0a53d')
            if len(overlays)<6:
                overlays.append(overlay.copy())
    report = dict(bar=BAR, hits=hits, total=total, photos=photos, eligible=eligible(hits,total,photos),
                  checkpoint_sha256=sha256((run/'best.pt').read_bytes()).hexdigest())
    graphics.mkdir(parents=True,exist_ok=True)
    for index,image in enumerate(overlays):
        image.save(graphics/f'validation_{index+1}.png')
    (run/'suggestion_eligibility.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"Validation-car mask hits: {hits}/{total}; bar >=90%, >=20 targets, >=6 photos (UNVALIDATED).")
    print('Suggestions eligible; explicit --suggestions still required.' if report['eligible'] else 'Suggestions OFF: bar not met.')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--graphics',default='video/graphics')
    args=parser.parse_args()
    validate(args.run,args.graphics)
