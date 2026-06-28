#!/usr/bin/env python3
"""Train the sklearn injection classifier and save to app/data/models/."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import classification_report  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402

from app.services.guard.training_data import BENIGN_EXAMPLES, UNSAFE_EXAMPLES  # noqa: E402

MODEL_DIR = BACKEND_ROOT / "app" / "data" / "models"
MODEL_PATH = MODEL_DIR / "injection_classifier.joblib"


def build_dataset() -> tuple[list[str], list[int]]:
    texts = list(BENIGN_EXAMPLES) + list(UNSAFE_EXAMPLES)
    labels = [0] * len(BENIGN_EXAMPLES) + [1] * len(UNSAFE_EXAMPLES)
    return texts, labels


def main() -> int:
    texts, labels = build_dataset()
    x_train, x_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    max_features=8000,
                    sublinear_tf=True,
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )
    pipeline.fit(x_train, y_train)
    preds = pipeline.predict(x_test)
    print(classification_report(y_test, preds, target_names=["benign", "unsafe"]))

    import joblib

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())