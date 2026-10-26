"""Optional reuse of body points for the same photo, plus a warmup using installed weights."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from threading import Lock


class PoseCache:
    def __init__(self,predict):
        self.predict=predict
        self.key=None
        self.value=None
        self.lock=Lock()

    def get(self,image):
        key=sha256(str((image.shape,str(image.dtype))).encode()+image.tobytes()).digest()
        with self.lock:
            if key!=self.key:
                value=self.predict(image)
                self.key,self.value=key,deepcopy(value)
            # WHY: return a copy so one caller cannot mess up the body points the next caller gets.
            return deepcopy(self.value)


def warm_models():
    import numpy as np
    from app.core.pose import get_keypoints
    from app.core.segment import segment
    root=Path(__file__).resolve().parents[1]
    cache=Path.home()/'.cache/rtmlib/hub/checkpoints'
    required=[root/'.venv/models/mobile_sam.pt',cache/'yolox_m_8xb8-300e_humanart-c2c7a14a.onnx',cache/'rtmpose-m_simcc-body7_pt-body7_420e-256x192-e48f03d0_20230504.onnx']
    if any(not path.is_file() for path in required):
        raise ValueError('Warmup requires existing cached models; no downloads attempted.')
    image=np.full((260,240,3),128,np.uint8)
    get_keypoints(image)
    segment(image,[dict(x=100,y=80,label=1)])
