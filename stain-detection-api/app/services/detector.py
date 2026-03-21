import os
import time
import numpy as np
import onnxruntime as ort
from PIL import Image

CLASSES = ["stain"]
MODEL_PATH = os.getenv("MODEL_PATH", "models/stain_detection_best.onnx")
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.25"))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.25"))
IMG_SIZE = 640


def _letterbox(img: np.ndarray, target: int = IMG_SIZE):
    """비율 유지 리사이즈 후 정사각형 패딩."""
    h, w = img.shape[:2]
    ratio = min(target / h, target / w)
    new_w, new_h = int(w * ratio), int(h * ratio)
    img = np.array(Image.fromarray(img).resize((new_w, new_h), Image.BILINEAR))
    pad_top = (target - new_h) // 2
    pad_left = (target - new_w) // 2
    padded = np.full((target, target, 3), 114, dtype=np.uint8)
    padded[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = img
    return padded, ratio, (pad_left, pad_top)


def _xywh2xyxy(boxes: np.ndarray) -> np.ndarray:
    out = boxes.copy()
    out[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
    out[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
    out[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
    out[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
    return out


def _nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float) -> list:
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        order = order[1:][iou <= iou_threshold]
    return keep


def _scale_boxes(boxes: np.ndarray, ratio: float, pad: tuple, orig_w: int, orig_h: int) -> np.ndarray:
    pad_left, pad_top = pad
    boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_left) / ratio
    boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_top) / ratio
    boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, orig_w)
    boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, orig_h)
    return boxes


class YOLOv12Detector:
    def __init__(self):
        available = ort.get_available_providers()
        providers = [p for p in ["CUDAExecutionProvider", "CPUExecutionProvider"] if p in available]
        self.session = ort.InferenceSession(MODEL_PATH, providers=providers)
        self.input_name = self.session.get_inputs()[0].name

    def predict(self, image: Image.Image) -> tuple:
        t0 = time.perf_counter()

        img_rgb = np.array(image.convert("RGB"))
        orig_h, orig_w = img_rgb.shape[:2]

        letterboxed, ratio, pad = _letterbox(img_rgb)
        tensor = letterboxed.transpose(2, 0, 1)[np.newaxis].astype(np.float32) / 255.0

        # YOLOv12 ONNX 출력: (1, 4+nc, num_proposals) — 전치(transpose) 필요
        raw = self.session.run(None, {self.input_name: tensor})[0]
        detections = self._postprocess(raw[0], orig_w, orig_h, ratio, pad)

        inference_ms = (time.perf_counter() - t0) * 1000
        return detections, inference_ms

    def _postprocess(self, output: np.ndarray, orig_w, orig_h, ratio, pad) -> list:
        # output shape: (4+nc, num_proposals) → transpose → (num_proposals, 4+nc)
        preds = output.T  # (num_proposals, 4+nc)

        boxes_xywh = preds[:, :4]
        class_scores = preds[:, 4:]  # YOLOv12은 objectness 없이 클래스 점수만 존재

        confidences = class_scores.max(axis=1)
        class_ids = class_scores.argmax(axis=1)

        mask = confidences > CONF_THRESHOLD
        if not mask.any():
            return []

        boxes_xywh = boxes_xywh[mask]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        boxes = _xywh2xyxy(boxes_xywh)
        keep = _nms(boxes, confidences, IOU_THRESHOLD)
        boxes = _scale_boxes(boxes[keep], ratio, pad, orig_w, orig_h)
        confidences = confidences[keep]
        class_ids = class_ids[keep]

        results = []
        for box, conf, cls_id in zip(boxes, confidences, class_ids):
            label = CLASSES[int(cls_id)] if int(cls_id) < len(CLASSES) else str(cls_id)
            results.append({
                "label": label,
                "confidence": float(conf),
                "bbox": {
                    "x1": float(box[0]),
                    "y1": float(box[1]),
                    "x2": float(box[2]),
                    "y2": float(box[3]),
                },
            })
        return results


# 앱 시작 시 1회 로드
detector = YOLOv12Detector()
