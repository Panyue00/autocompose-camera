"""照片存储 — 文件管理 + 元数据"""

import os
import json
import time
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class PhotoMeta:
    path: str
    timestamp: float
    width: int
    height: int
    score: float = 0.0
    scene_type: str = "unknown"
    has_crop: bool = False
    crop_meta: dict | None = None


class PhotoRepository:
    """照片仓库 — 管理照片文件和元数据"""

    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".autocompose")
        self.photo_dir = os.path.join(self.data_dir, "photos")
        self.meta_file = os.path.join(self.data_dir, "photo_meta.json")
        os.makedirs(self.photo_dir, exist_ok=True)

    def save_photo(self, image: np.ndarray, score: float = 0.0,
                   scene_type: str = "unknown") -> PhotoMeta:
        """保存照片 + 元数据"""
        timestamp = time.time()
        name = time.strftime("AC_%Y%m%d_%H%M%S") + f"_{int(timestamp * 1000) % 1000:03d}.jpg"
        path = os.path.join(self.photo_dir, name)

        h, w = image.shape[:2]
        try:
            import cv2
            cv2.imwrite(path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                       [cv2.IMWRITE_JPEG_QUALITY, 95])
        except ImportError:
            from PIL import Image
            Image.fromarray(image).save(path, "JPEG", quality=95)

        meta = PhotoMeta(
            path=path, timestamp=timestamp,
            width=w, height=h, score=score, scene_type=scene_type
        )
        self._save_meta(meta)
        return meta

    def list_photos(self) -> list[PhotoMeta]:
        """列出所有照片"""
        meta_dicts = self._load_all_meta()
        return [PhotoMeta(**m) for m in meta_dicts]

    def get_photo_meta(self, path: str) -> PhotoMeta | None:
        """获取单张照片的元数据"""
        for m in self.list_photos():
            if m.path == path:
                return m
        return None

    def load_image(self, path: str) -> np.ndarray | None:
        """加载照片为 numpy 数组"""
        try:
            import cv2
            return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
        except ImportError:
            from PIL import Image
            return np.array(Image.open(path).convert("RGB"))

    def _load_all_meta(self) -> list[dict]:
        """加载全部元数据"""
        if not os.path.exists(self.meta_file):
            return []
        try:
            with open(self.meta_file, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_meta(self, meta: PhotoMeta):
        """追加一条元数据"""
        all_meta = self._load_all_meta()
        all_meta.append(asdict(meta))
        with open(self.meta_file, "w") as f:
            json.dump(all_meta, f, indent=2)
