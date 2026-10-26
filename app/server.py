"""The local photo/tap API. Photos stay in memory unless someone explicitly saves labels."""
import argparse
from pathlib import Path

from flask import Flask, jsonify, request
import numpy as np
from PIL import UnidentifiedImageError
from waitress import serve

from app.core.pose import get_keypoints
from app.core.segment import segment
from app.core.mask_quality import rejection as reject_mask
from app.core.rules import evaluate, SEATS
from app.core.quality import evaluate_photo
from app.config import flags_with,load_flags,FLAGS_FILE,NORMAL_DEFAULT_FLAGS
from app.core.experiments import evaluate_with_flags
from app.core.suggest import load_predictor, suggest_taps
from app.labeling import save_session
from app.media import decode_masks, image_from_data, png_data
from app.usability import append_record
from app.runtime import PoseCache,warm_models
from app.core.prompts import refinement_prompts
from app.core.measurement_geometry import geometry_for

SERVER_OPTIONS = {"threads": 2, "max_request_body_size": 16*1024*1024,
                  "inbuf_overflow": 32*1024*1024, "outbuf_overflow": 32*1024*1024}

def create_app(segment_model="mobile_sam", suggestions=False, tap_checkpoint=None, flags=None, usability_path=None):
    # WHY: use the normal reference guesses unless the caller explicitly asks for other flags.
    experiment_flags = flags_with(NORMAL_DEFAULT_FLAGS if flags is None else flags)
    pose_cache = PoseCache(lambda image:get_keypoints(image))
    def body_points(image,data,allow_cache=True):
        if allow_cache and experiment_flags['POSE_CACHE'] and data.get('reuse_pose') is True:
            return pose_cache.get(image)
        return get_keypoints(image)
    predictor = load_predictor(tap_checkpoint) if suggestions else None
    web = Flask(__name__, static_folder="static", static_url_path="/static")
    web.config["MAX_CONTENT_LENGTH"] = 16*1024*1024
    web.config['SEATCHECK_FLAGS']=experiment_flags.copy()

    @web.after_request
    def no_store(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @web.errorhandler(ValueError)
    @web.errorhandler(KeyError)
    @web.errorhandler(TypeError)
    @web.errorhandler(UnidentifiedImageError)
    def bad_input(error):
        return jsonify(error=str(error)), 400

    @web.errorhandler(413)
    def too_large(error):
        return jsonify(error="Photo request is too large. Choose a smaller photo."), 413

    @web.get("/")
    def index():
        return web.send_static_file("index.html")

    @web.post("/api/pose")
    def pose():
        data=request.get_json()
        image = image_from_data(data["image"])
        points = body_points(image,data)
        result = dict(keypoints=points)
        if experiment_flags['MULTI_TAP']:
            result['features']=dict(multi_tap=True,validated=False)
        if suggestions:
            result["suggestions"] = suggest_taps(image, points, predictor)
        return jsonify(result)

    @web.post("/api/segment")
    def masks():
        data = request.get_json()
        image = image_from_data(data["image"])
        taps=data['taps']
        points=None
        if 'item_type' in data:
            points=body_points(image,data)
            taps=refinement_prompts(points,taps,data['item_type'])
        # WHY: both modes pick strap masks the same way; saving still needs a person to confirm one.
        context=dict(keypoints=points,item_type=data['item_type']) if 'item_type' in data else {}
        mask = segment(image, taps, model=segment_model, **context)
        if "item_type" in data:
            blocked = reject_mask(mask, points if points is not None else body_points(image,data), data["item_type"])
            if blocked:
                return jsonify(blocked)
        return jsonify(mask=png_data(mask.astype(np.uint8)*255))

    def inputs(allow_cache=True):
        data = request.get_json()
        if data["seat_type"] not in SEATS:
            raise ValueError("Choose a seat type.")
        image = image_from_data(data["image"])
        masks = decode_masks(data.get("masks", {}), image.shape)
        # WHY: get points for this photo; old browser dots must not end up measuring a different photo.
        points = body_points(image,data,allow_cache)
        return data, image, masks, points

    @web.post("/api/results")
    def results():
        data, image, masks, points = inputs()
        # WHY: labels keep the raw checks and their origin, even when normal mode has an experiment ON.
        checks=evaluate_with_flags(image, points, masks, data["seat_type"], None if data.get('label_mode') is True else experiment_flags)
        # WHY: X-ray geometry sits beside the results, not inside them; labeling gets the same records.
        if data.get('label_mode') is True:
            return jsonify(checks=checks)
        return jsonify(checks=checks,geometry=geometry_for(points,masks,checks,image.shape))

    @web.post("/api/label")
    def label():
        data, image, masks, points = inputs(allow_cache=False)
        if data.get("label_mode") is not True:
            raise ValueError("Open ?label=1 and explicitly choose to save labels.")
        meta = dict(data.get("metadata", {}), seat_type=data["seat_type"])
        return jsonify(save_session(image, masks, points, meta, receipt=True))

    @web.post('/api/user-test')
    def usability():
        append_record(request.get_json(),usability_path or Path(__file__).resolve().parents[1]/'data/private/user_test.csv')
        return jsonify(recorded=True)

    return web


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--segment-model", choices=["mobile_sam", "sam"], default="mobile_sam")
    parser.add_argument("--suggestions", action="store_true", help="Enable parent-reviewed proposals from a real trained checkpoint.")
    parser.add_argument("--tap-checkpoint", help="Path to a real training run's best.pt; smoke checkpoints are rejected.")
    parser.add_argument('--pose-cache',action='store_true',default=None,help='Explicit opt-in to exact-image pose reuse; default OFF.')
    parser.add_argument('--flags-file',type=Path,default=FLAGS_FILE,help='Local boolean flag config; absent file means all OFF.')
    parser.add_argument('--warm-models',action='store_true',help='Warm installed cached models without downloading weights.')
    args = parser.parse_args()
    try:
        configured=load_flags(args.flags_file)
        if args.pose_cache is True:
            configured['POSE_CACHE']=True
        print('Flags: '+', '.join(f'{name}={"ON" if value else "OFF"}' for name,value in sorted(configured.items())),flush=True)
        if args.warm_models:
            warm_models()
        web = create_app(args.segment_model, args.suggestions, args.tap_checkpoint,flags=configured)
    except (ValueError, KeyError, TypeError, OSError, RuntimeError) as error:
        parser.exit(2, str(error)+"\n")
    print(f"SeatCheck local server on http://{args.host}:{args.port}", flush=True)
    # WHY: Waitress can spill large requests to disk; these buffers keep accepted photos in memory.
    serve(web, host=args.host, port=args.port, **SERVER_OPTIONS)
