"""TF-IDF + logistic regression classifier for prompt-injection detection."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

ML_RULE_ID = "ml:unsafe"

_MODEL_LOCK = threading.Lock()
_PIPELINE = None
_LOAD_ATTEMPTED = False


@dataclass(frozen=True)
class MLPrediction:
    enabled: bool
    loaded: bool
    label: str  # "benign" | "unsafe"
    unsafe_score: float  # P(unsafe), 0.0 when disabled/unloaded


def _default_model_path() -> Path:
    return settings.ML_GUARD_MODEL_PATH


def _load_pipeline():
    global _PIPELINE, _LOAD_ATTEMPTED
    with _MODEL_LOCK:
        if _LOAD_ATTEMPTED:
            return _PIPELINE
        _LOAD_ATTEMPTED = True
        path = _default_model_path()
        if not path.exists():
            logger.warning("ML guard model not found at %s — classifier disabled.", path)
            return None
        try:
            import joblib

            _PIPELINE = joblib.load(path)
            logger.info("ML guard model loaded from %s", path)
        except Exception:
            logger.exception("Failed to load ML guard model from %s", path)
            _PIPELINE = None
        return _PIPELINE


def reload_model() -> bool:
    """Force reload (used in tests). Returns True if model loaded."""
    global _PIPELINE, _LOAD_ATTEMPTED
    with _MODEL_LOCK:
        _PIPELINE = None
        _LOAD_ATTEMPTED = False
    return _load_pipeline() is not None


def predict_unsafe(text: str) -> MLPrediction:
    if not settings.ML_GUARD_ENABLED:
        return MLPrediction(enabled=False, loaded=False, label="benign", unsafe_score=0.0)

    pipeline = _load_pipeline()
    if pipeline is None:
        return MLPrediction(enabled=True, loaded=False, label="benign", unsafe_score=0.0)

    try:
        proba = pipeline.predict_proba([text])[0]
        classes = list(pipeline.classes_)
        unsafe_idx = classes.index(1) if 1 in classes else 0
        unsafe_score = float(proba[unsafe_idx])
        label = "unsafe" if unsafe_score >= settings.ML_GUARD_THRESHOLD else "benign"
        return MLPrediction(
            enabled=True,
            loaded=True,
            label=label,
            unsafe_score=unsafe_score,
        )
    except Exception:
        logger.exception("ML guard prediction failed")
        return MLPrediction(enabled=True, loaded=True, label="benign", unsafe_score=0.0)


def ml_decision(unsafe_score: float) -> str | None:
    """Return block, warn, or None (allow) based on configured thresholds."""
    if unsafe_score >= settings.ML_GUARD_THRESHOLD:
        return "block"
    if unsafe_score >= settings.ML_GUARD_WARN_THRESHOLD:
        return "warn"
    return None


def classifier_status() -> dict:
    pipeline = _load_pipeline() if settings.ML_GUARD_ENABLED else None
    path = _default_model_path()
    return {
        "enabled": settings.ML_GUARD_ENABLED,
        "loaded": pipeline is not None,
        "model_path": str(path),
        "model_exists": path.exists(),
        "backend": settings.ML_GUARD_BACKEND,
        "block_threshold": settings.ML_GUARD_THRESHOLD,
        "warn_threshold": settings.ML_GUARD_WARN_THRESHOLD,
        "rule_id": ML_RULE_ID,
    }