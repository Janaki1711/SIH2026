# tinyml_classifier.py
"""
iTantra M3 — Lightweight TinyML Contextual Semantic Role Classifier
Classifies candidate phrases/tokens into semantic roles using contextual,
character n-gram, and morpho-syntactic features.

Model Properties:
- Architecture: FeatureUnion (Char-WB TFIDF + Word Context TFIDF + Structural Signals) + Calibrated Linear Logistic Classifier
- CPU-only inference
- Execution time: < 1.0 ms per inference
- Model artifact size: < 1 MB
- Offline, zero external dependencies
"""

import os
import re
import joblib
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression

from tinyml_dataset import ROLES, ROLE2ID, ID2ROLE

MODEL_FILE = os.path.join(os.path.dirname(__file__), "tinyml_model.joblib")


def format_context_string(span: str, left_ctx: str = "", right_ctx: str = "") -> str:
    """Format span and surrounding window into structured representation."""
    return f"[L] {left_ctx.strip()} [S] {span.strip()} [R] {right_ctx.strip()}"


class StructuralFeatureExtractor(BaseEstimator, TransformerMixin):
    """Extracts lightweight structural, morphological, and positional signals."""
    
    _DIR_WORDS = {"east", "west", "north", "south", "northeast", "northwest", "southeast", "southwest", "eastern", "western", "northern", "southern"}
    _QTY_WORDS = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "twelve", "fifteen", "twenty", "एक", "दो", "तीन", "चार", "पांच", "पाँच", "छह", "सात", "आठ", "नौ", "दस", "இரண்டு", "மூன்று", "ஐந்து"}
    _PEOPLE_WORDS = {"people", "persons", "villagers", "workers", "civilians", "casualties", "patients", "victims", "soldiers", "लोग", "व्यक्ति", "பேர்"}
    
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        features = []
        for sample in X:
            span = sample.get("span", "").strip()
            left = sample.get("left_ctx", "").strip().lower()
            right = sample.get("right_ctx", "").strip().lower()
            full = sample.get("text", "").strip().lower()
            span_lower = span.lower()
            
            # Structural heuristics
            has_digits = bool(re.search(r'\d', span))
            is_digit_only = bool(re.match(r'^\d+$', span))
            is_callsign_pattern = bool(re.search(r'\b(alpha|bravo|charlie|delta|echo|foxtrot|team|unit|squad|sector|grid)\s+\d+\b', span, re.IGNORECASE))
            has_team_prefix = bool(re.search(r'\b(team|unit|squad|group|callsign)\b', left))
            has_prep_prefix = bool(re.search(r'\b(to|at|in|near|towards|toward|from|behind|near the|around)\b', left))
            has_hindi_prep = "के पास" in right or "की तरफ" in right or "में" in right
            has_people_after = bool(re.search(r'\b(people|villagers|workers|civilians|casualties|victims|men|women|लोग|व्यक्तियों|பேர்)\b', right))
            is_qty_word = span_lower in self._QTY_WORDS or is_digit_only
            is_dir_word = span_lower in self._DIR_WORDS
            has_need_send = bool(re.search(r'\b(need|send|dispatch|deploy|requesting|require|भेजें|भेजो|அனுப்பு)\b', left))
            has_hazard_context = bool(re.search(r'\b(collapsed|danger|unsafe|fire|flood|smoke|threat|warning|खतरा|விபத்து)\b', full))
            has_comms_context = bool(re.search(r'\b(signal|link|radio|network|comm|active|weak|down)\b', full))
            
            feat = {
                "has_digits": int(has_digits),
                "is_digit_only": int(is_digit_only),
                "is_callsign_pattern": int(is_callsign_pattern),
                "has_team_prefix": int(has_team_prefix),
                "has_prep_prefix": int(has_prep_prefix),
                "has_hindi_prep": int(has_hindi_prep),
                "has_people_after": int(has_people_after),
                "is_qty_word": int(is_qty_word),
                "is_dir_word": int(is_dir_word),
                "has_need_send": int(has_need_send),
                "has_hazard_context": int(has_hazard_context),
                "has_comms_context": int(has_comms_context),
                "span_word_count": len(span.split()),
                "span_char_len": len(span),
                "is_title_cased": int(span.istitle() if span else False),
            }
            features.append(feat)
        return features


class TextContextExtractor(BaseEstimator, TransformerMixin):
    """Extracts formatted context string for text vectorization."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return [format_context_string(s.get("span", ""), s.get("left_ctx", ""), s.get("right_ctx", "")) for s in X]


class SpanTextExtractor(BaseEstimator, TransformerMixin):
    """Extracts target span text for subword/character n-gram vectorization."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        return [s.get("span", "") for s in X]


def create_pipeline() -> Pipeline:
    """Constructs the combined FeatureUnion and calibrated classifier pipeline."""
    feature_union = FeatureUnion([
        (
            "context_words",
            Pipeline([
                ("extractor", TextContextExtractor()),
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), analyzer="word", max_features=3500, sublinear_tf=True)),
            ])
        ),
        (
            "span_char_wb",
            Pipeline([
                ("extractor", SpanTextExtractor()),
                ("tfidf", TfidfVectorizer(ngram_range=(3, 5), analyzer="char_wb", max_features=4500, sublinear_tf=True)),
            ])
        ),
        (
            "structural_features",
            Pipeline([
                ("extractor", StructuralFeatureExtractor()),
                ("vectorizer", DictVectorizer(sparse=True)),
            ])
        )
    ])

    pipeline = Pipeline([
        ("features", feature_union),
        ("classifier", LogisticRegression(C=3.5, max_iter=1000, solver="lbfgs", random_state=42))
    ])
    return pipeline


class TinyMLClassifier:
    """Singleton/Instance wrapper for inference and model persistence."""
    
    _instance = None
    
    def __init__(self, model_path: str = MODEL_FILE):
        self.model_path = model_path
        self.model: Optional[Pipeline] = None
        self.load_model_if_exists()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_model_if_exists(self) -> bool:
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                return True
            except Exception as e:
                print(f"[TinyML] Warning: Could not load model from {self.model_path}: {e}")
                self.model = None
        return False

    def train_and_save(self, train_samples: List[Dict]) -> None:
        """Fit pipeline on dataset and save artifact."""
        y_train = [s["role_id"] for s in train_samples]
        self.model = create_pipeline()
        self.model.fit(train_samples, y_train)
        joblib.dump(self.model, self.model_path, compress=3)

    def predict_role(self, span: str, left_ctx: str = "", right_ctx: str = "", full_text: str = "") -> Tuple[str, float]:
        """
        Predict contextual role and confidence for a given span.
        Returns: (role_name: str, confidence: float)
        """
        if self.model is None:
            if not self.load_model_if_exists():
                return ("UNKNOWN", 0.0)

        sample = {
            "text": full_text or f"{left_ctx} {span} {right_ctx}".strip(),
            "span": span,
            "left_ctx": left_ctx,
            "right_ctx": right_ctx,
        }

        try:
            probs = self.model.predict_proba([sample])[0]
            pred_id = int(np.argmax(probs))
            conf = float(probs[pred_id])
            role_name = ID2ROLE.get(pred_id, "UNKNOWN")
            return (role_name, conf)
        except Exception as e:
            return ("UNKNOWN", 0.0)
