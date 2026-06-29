"""Gemini Vision API 客户端 — 构图分析增强"""

import base64
import numpy as np
from io import BytesIO


class GeminiClient:
    """Gemini 2.0 Flash Vision — 提供自然语言构图解释"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.available = False
        self._model = None

        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self._model = genai.GenerativeModel("gemini-2.0-flash-exp")
                self.available = True
            except ImportError:
                pass
            except Exception:
                pass

    def analyze_composition(self, image: np.ndarray,
                            top_results: list) -> dict:
        """发送给 Gemini 分析构图方案"""
        if not self.available or self._model is None:
            return {"error": "Gemini not available"}

        # 编码图片
        try:
            from PIL import Image
            pil = Image.fromarray(image)
            # 缩放到 1024px
            w, h = pil.size
            if max(w, h) > 1024:
                ratio = 1024 / max(w, h)
                pil = pil.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
            buf = BytesIO()
            pil.save(buf, format="JPEG", quality=85)
            img_b64 = base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            return {"error": str(e)}

        # 构建 prompt
        results_text = ""
        for i, r in enumerate(top_results):
            results_text += f"方案{i+1}: 得分={r.total_score:.0f}/100, "
            results_text += f"最佳规则={max(r.rule_scores, key=r.rule_scores.get)}, "
            results_text += f"裁剪框=({r.candidate.x},{r.candidate.y},{r.candidate.width}x{r.candidate.height})\n"

        prompt = f"""你是一个专业摄影构图评审。以下是一张照片和3个自动构图裁剪方案。

{results_text}

请选择最佳方案，给出:
1. best_pick: 方案编号 (1/2/3)
2. explanation: 50字以内的构图解释
3. poetic_hint: 一句诗意构图建议

只用中文回复，JSON格式: {{"best_pick": 1, "explanation": "...", "poetic_hint": "..."}}"""

        try:
            response = self._model.generate_content([prompt, img_b64])
            import json
            return json.loads(response.text.strip().strip("```json").strip("```"))
        except Exception as e:
            return {"error": str(e), "best_pick": 1}
