# tinyml_v3_adapter.py
# iTantra M3 -- V3 Isolated Candidate Adapter
# Exposes predict_role() with same interface as V2 TinyMLClassifier.
# hybrid_engine.py is NOT modified. This is for future benchmarking only.

import os
import numpy as np
from typing import Tuple

from tinyml_model_v3 import (
    CharTokenizer, TFLiteInferenceEngine,
    format_context_string,
    MODEL_V3_INT8_TF, MODEL_V3_FP32_TF, TOKENIZER_V3,
    MAX_LEN,
)
from tinyml_dataset import ID2ROLE

_DEFAULT_MODEL = MODEL_V3_INT8_TF


class TinyMLV3Adapter:
    """
    Isolated V3 candidate adapter.
    Interface identical to V2 TinyMLClassifier.predict_role().
    Confidence >= 0.70 accepted; < 0.70 falls back to rule engine.
    Does NOT modify hybrid_engine.py.
    """
    _instance = None

    def __init__(self, model_path: str = _DEFAULT_MODEL):
        self.model_path = model_path
        self._engine    = None
        self._tokenizer = None
        self._load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load(self):
        if not os.path.exists(self.model_path):
            print(f"[V3 Adapter] Model not found: {self.model_path}")
            return
        if not os.path.exists(TOKENIZER_V3):
            print(f"[V3 Adapter] Tokenizer not found: {TOKENIZER_V3}")
            return
        self._tokenizer = CharTokenizer.load(TOKENIZER_V3)
        self._engine    = TFLiteInferenceEngine(model_path=self.model_path)
        print(f"[V3 Adapter] Loaded: {os.path.basename(self.model_path)}")

    def predict_role(self, span: str, left_ctx: str = '', right_ctx: str = '',
                     full_text: str = '') -> Tuple[str, float]:
        """Predict semantic role. Returns (role_name, confidence)."""
        if self._engine is None or self._tokenizer is None:
            return ('UNKNOWN', 0.0)
        text = format_context_string(span, left_ctx, right_ctx)
        x    = np.array(self._tokenizer.encode(text, MAX_LEN), dtype=np.int32)
        try:
            probs   = self._engine.predict_proba_single(x)
            pred_id = int(np.argmax(probs))
            conf    = float(probs[pred_id])
            return (ID2ROLE.get(pred_id, 'UNKNOWN'), conf)
        except Exception as e:
            print(f"[V3 Adapter] Inference error: {e}")
            return ('UNKNOWN', 0.0)

    @property
    def is_ready(self) -> bool:
        return self._engine is not None and self._tokenizer is not None
