"""TFLite 模型加载与推理"""

import numpy as np

HAS_TFLITE = False
try:
    import tflite_runtime.interpreter as tflite
    HAS_TFLITE = True
except ImportError:
    pass


class TFLiteModel:
    """TFLite 模型包装器"""

    def __init__(self, model_path: str, input_mean: float = 0.0,
                 input_std: float = 1.0, threads: int = 4):
        self.model_path = model_path
        self.input_mean = input_mean
        self.input_std = input_std
        self.interpreter = None
        if HAS_TFLITE:
            self.interpreter = tflite.Interpreter(
                model_path=model_path,
                num_threads=threads
            )
            self.interpreter.allocate_tensors()
            self._input_details = self.interpreter.get_input_details()
            self._output_details = self.interpreter.get_output_details()

    def predict(self, image: np.ndarray) -> np.ndarray:
        """推理单张图片，返回输出 tensor"""
        if self.interpreter is None:
            return np.array([])

        # 预处理
        input_shape = self._input_details[0]["shape"]
        h, w = input_shape[1], input_shape[2]

        # Resize
        try:
            import cv2
            resized = cv2.resize(image, (w, h))
        except ImportError:
            from PIL import Image
            pil = Image.fromarray(image)
            resized = np.array(pil.resize((w, h), Image.LANCZOS))

        # Normalize
        normalized = (resized.astype(np.float32) / 255.0 - self.input_mean) / self.input_std

        # Add batch dim
        input_data = np.expand_dims(normalized, axis=0)

        self.interpreter.set_tensor(self._input_details[0]["index"], input_data)
        self.interpreter.invoke()
        return self.interpreter.get_tensor(self._output_details[0]["index"])[0]


class DeepLabV3(TFLiteModel):
    """语义分割模型 — 21 类输出"""

    def predict(self, image: np.ndarray) -> np.ndarray:
        output = super().predict(image)
        return np.argmax(output, axis=-1).astype(np.uint8)  # H×W int labels


class MiDaS(TFLiteModel):
    """深度估计模型 — 相对深度图"""

    def predict(self, image: np.ndarray) -> np.ndarray:
        output = super().predict(image)
        if output.ndim == 3:
            output = output[:, :, 0]
        # 归一化到 0..1
        output = (output - output.min()) / (output.max() - output.min() + 1e-10)
        return output


class BASNet(TFLiteModel):
    """显著性检测 — 输出 0..1 热力图"""

    def predict(self, image: np.ndarray) -> np.ndarray:
        output = super().predict(image)
        if output.ndim == 3:
            output = output[:, :, 0]
        return np.clip(output, 0, 1)
