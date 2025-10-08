import os
from typing import Optional
import numpy as np
import cv2
try:
    import mediapipe as mp
except Exception:
    mp = None


class PersonSegmenter:
    """
    Segmenta a la persona (primer plano) usando MediaPipe Selfie Segmentation (si está disponible)
    y compone sobre un fondo dado (imagen) o color sólido.
    """
    def __init__(self, background_image: Optional[str] = None, bg_color=(16, 19, 24)):
        self.bg_color = bg_color
        # Use ImagePaths.init_img if available
        try:
            from process.gui.image_paths import ImagePaths
            default_bg = ImagePaths().init_img
        except Exception:
            default_bg = None
        self.bg_image_path = background_image or os.getenv('GUI_BACKGROUND', default_bg or '')
        self.bg_image = None
        if self.bg_image_path and os.path.exists(self.bg_image_path):
            self.bg_image = cv2.imread(self.bg_image_path)

        self.seg = None
        if mp is not None:
            try:
                self.seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
            except Exception:
                self.seg = None

    def apply(self, bgr_frame: np.ndarray) -> np.ndarray:
        if bgr_frame is None or bgr_frame.size == 0:
            return bgr_frame
        if self.seg is None:
            # Sin modelo: devolver el frame original
            return bgr_frame
        # MediaPipe requiere RGB
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        res = self.seg.process(rgb)
        if res.segmentation_mask is None:
            return bgr_frame
        mask = res.segmentation_mask
        h, w = bgr_frame.shape[:2]
        mask_3 = np.dstack([mask]*3)
        # Preparar fondo (imagen escalada o color sólido)
        if self.bg_image is not None:
            bg = cv2.resize(self.bg_image, (w, h), interpolation=cv2.INTER_CUBIC)
        else:
            bg = np.full((h, w, 3), self.bg_color, dtype=np.uint8)
        # Alpha matting simple
        fg = bgr_frame.astype(np.float32)
        bg = bg.astype(np.float32)
        m = np.clip(mask_3, 0.0, 1.0)
        out = fg * m + bg * (1.0 - m)
        return out.astype(np.uint8)
