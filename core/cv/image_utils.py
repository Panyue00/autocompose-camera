"""OpenCV 图像处理工具 — 裁剪/透视/调色"""

import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


def crop_image(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
    """裁剪图片到指定矩形"""
    return image[y:y+h, x:x+w]


def resize_to_fit(image: np.ndarray, max_width: int = 1024) -> np.ndarray:
    """等比缩放"""
    h, w = image.shape[:2]
    if w <= max_width:
        return image
    ratio = max_width / w
    new_w, new_h = int(w * ratio), int(h * ratio)
    if HAS_CV2:
        return cv2.resize(image, (new_w, new_h))
    from PIL import Image
    pil = Image.fromarray(image)
    return np.array(pil.resize((new_w, new_h), Image.LANCZOS))


def correct_horizon(image: np.ndarray, angle_degrees: float) -> np.ndarray:
    """旋转图像矫正水平"""
    if not HAS_CV2 or abs(angle_degrees) < 0.5:
        return image
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
    return cv2.warpAffine(image, matrix, (w, h), borderMode=cv2.BORDER_REPLICATE)


def correct_perspective(image: np.ndarray, src_points: np.ndarray,
                        dst_points: np.ndarray) -> np.ndarray:
    """透视矫正"""
    if not HAS_CV2:
        return image
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    h, w = image.shape[:2]
    return cv2.warpPerspective(image, matrix, (w, h))


def adjust_color(image: np.ndarray, brightness: float = 0.0,
                 contrast: float = 1.0, saturation: float = 1.0,
                 warmth: float = 0.0) -> np.ndarray:
    """基础调色"""
    if not HAS_CV2:
        return image

    result = image.astype(np.float32)

    # 亮度 + 对比度
    result = result * contrast + brightness * 255

    # 饱和度 (转 HSV)
    hsv = cv2.cvtColor(result.clip(0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1].astype(np.float32) * saturation, 0, 255).astype(np.uint8)
    result = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)

    # 色温: R += warmth, B -= warmth
    result[:, :, 0] += warmth * 20
    result[:, :, 2] -= warmth * 20

    return result.clip(0, 255).astype(np.uint8)
