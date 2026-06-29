"""几何结构分析器 — 引导线/对称/水平检测 (使用 OpenCV)"""

import numpy as np
from .models import GeomStructure, Line2D, SymmetryAxis, VanishingPoint

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class GeometricAnalyzer:
    """几何结构分析器 — 提取引导线、对称轴、水平线"""

    def __init__(self):
        self.available = HAS_CV2

    def analyze(self, image: np.ndarray) -> GeomStructure:
        """分析图片几何结构"""
        if not HAS_CV2:
            return GeomStructure()

        result = GeomStructure()

        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        h, w = gray.shape

        # 引导线检测
        result.leading_lines = self._detect_leading_lines(gray, h, w)

        # 对称轴检测
        result.symmetry_axes = self._detect_symmetry(gray, h, w)

        # 水平线检测
        result.horizon_y, result.tilt_angle = self._detect_horizon(gray, h, w)

        # 消失点聚类
        if len(result.leading_lines) >= 2:
            result.vanishing_points = self._cluster_vanishing_points(
                result.leading_lines, w, h
            )

        return result

    def _detect_leading_lines(self, gray: np.ndarray, h: int, w: int) -> list[Line2D]:
        """Canny + 概率霍夫变换检测引导线"""
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)
        edges = cv2.Canny(blurred, 50, 150)

        lines = cv2.HoughLinesP(
            edges, rho=1, theta=np.pi / 180, threshold=80,
            minLineLength=min(w, h) // 5, maxLineGap=15
        )

        if lines is None:
            return []

        result = []
        edge_strength = cv2.Sobel(gray, cv2.CV_32F, 1, 1)
        edge_mag = np.sqrt(edge_strength**2).astype(np.float32)

        for line in lines:
            x1, y1, x2, y2 = line[0]
            # 计算线段上的平均边缘强度
            points = np.linspace(0, 1, 10)
            strengths = []
            for t in points:
                px = int(x1 + t * (x2 - x1))
                py = int(y1 + t * (y2 - y1))
                if 0 <= px < w and 0 <= py < h:
                    strengths.append(edge_mag[py, px])
            saliency = np.mean(strengths) if strengths else 1.0
            saliency = min(1.0, saliency / 100.0)

            result.append(Line2D(
                x1=float(x1), y1=float(y1),
                x2=float(x2), y2=float(y2),
                saliency=float(saliency)
            ))

        return result

    def _detect_symmetry(self, gray: np.ndarray, h: int, w: int) -> list[SymmetryAxis]:
        """相位相关检测对称轴"""
        axes = []

        # 垂直对称: 左右翻转后进行相位相关
        flipped_h = np.fliplr(gray)
        if gray.shape == flipped_h.shape:
            shift = self._phase_correlation(gray, flipped_h)
            if shift is not None:
                dx, dy = shift
                axis_x = w / 2 + dx / 2
                strength = self._symmetry_strength(gray, flipped_h, shift)
                if strength > 0.3:
                    axes.append(SymmetryAxis(
                        x1=float(axis_x), y1=0.0,
                        x2=float(axis_x), y2=float(h),
                        strength=float(strength),
                        axis_type="vertical"
                    ))

        # 水平对称
        flipped_v = np.flipud(gray)
        if gray.shape == flipped_v.shape:
            shift = self._phase_correlation(gray, flipped_v)
            if shift is not None:
                dx, dy = shift
                axis_y = h / 2 + dy / 2
                strength = self._symmetry_strength(gray, flipped_v, shift)
                if strength > 0.3:
                    axes.append(SymmetryAxis(
                        x1=0.0, y1=float(axis_y),
                        x2=float(w), y2=float(axis_y),
                        strength=float(strength),
                        axis_type="horizontal"
                    ))

        return axes

    def _phase_correlation(self, img1: np.ndarray, img2: np.ndarray) -> tuple[float, float] | None:
        """相位相关: 返回 (dx, dy) 平移"""
        try:
            f1 = np.fft.fft2(img1.astype(np.float32))
            f2 = np.fft.fft2(img2.astype(np.float32))
            cross = f1 * np.conj(f2)
            cross /= (np.abs(cross) + 1e-10)
            result = np.fft.ifft2(cross)
            result = np.abs(np.fft.fftshift(result))
            peak = np.unravel_index(result.argmax(), result.shape)
            dx = peak[1] - result.shape[1] // 2
            dy = peak[0] - result.shape[0] // 2
            return float(dx), float(dy)
        except Exception:
            return None

    def _symmetry_strength(self, img1: np.ndarray, img2: np.ndarray,
                           shift: tuple[float, float]) -> float:
        """对称强度评估"""
        try:
            f1 = np.fft.fft2(img1.astype(np.float32))
            f2 = np.fft.fft2(img2.astype(np.float32))
            cross = f1 * np.conj(f2)
            cross /= (np.abs(cross) + 1e-10)
            result = np.abs(np.fft.ifft2(cross))
            peak = result.max()
            bg = np.mean(result)
            snr = peak / (bg + 1e-10)
            return min(1.0, snr / 10.0)
        except Exception:
            return 0.0

    def _detect_horizon(self, gray: np.ndarray, h: int, w: int) -> tuple[float | None, float]:
        """检测水平线和倾斜角"""
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100,
                                minLineLength=w // 3, maxLineGap=20)

        if lines is None:
            return None, 0.0

        angles = []
        y_positions = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # 接近水平的线 (-5° ~ 5°)
            if -5 < angle < 5:
                angles.append(angle)
                y_positions.append((y1 + y2) / 2)

        if angles:
            tilt = float(np.median(angles))
            horizon = float(np.median(y_positions))
            return horizon, tilt

        return None, 0.0

    def _cluster_vanishing_points(self, lines: list[Line2D],
                                  w: int, h: int) -> list[VanishingPoint]:
        """RANSAC 消失点聚类"""
        if len(lines) < 10:
            return []

        # 对每条线计算归一化方向向量，两两求交点
        intersections = []
        for i in range(len(lines)):
            li = lines[i]
            for j in range(i + 1, len(lines)):
                lj = lines[j]
                inter = self._line_intersection(li, lj)
                if inter is not None:
                    ix, iy = inter
                    if 0 <= ix <= w and 0 <= iy <= h:
                        intersections.append((ix, iy))

        if not intersections:
            return []

        # 简单聚类: 取最多交点的区域
        grid_size = 20
        grid = np.zeros((h // grid_size + 1, w // grid_size + 1))
        for ix, iy in intersections:
            grid_x = int(ix / grid_size)
            grid_y = int(iy / grid_size)
            if 0 <= grid_y < grid.shape[0] and 0 <= grid_x < grid.shape[1]:
                grid[grid_y, grid_x] += 1

        if grid.max() < 3:
            return []

        peak = np.unravel_index(grid.argmax(), grid.shape)
        vx = peak[1] * grid_size + grid_size / 2
        vy = peak[0] * grid_size + grid_size / 2
        conf = min(1.0, grid[peak] / 20.0)

        interior = (0.1 * w < vx < 0.9 * w and 0.1 * h < vy < 0.9 * h)

        return [VanishingPoint(
            x=float(vx), y=float(vy),
            confidence=float(conf),
            line_count=int(grid[peak]),
            is_interior=interior
        )]

    def _line_intersection(self, l1: Line2D, l2: Line2D) -> tuple[float, float] | None:
        """求两线段延长线的交点"""
        x1, y1, x2, y2 = l1.x1, l1.y1, l1.x2, l1.y2
        x3, y3, x4, y4 = l2.x1, l2.y1, l2.x2, l2.y2

        denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(denom) < 1e-10:
            return None

        px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
        py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
        return px, py
