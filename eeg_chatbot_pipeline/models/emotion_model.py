from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier


class EmotionModel:
    """
    Input should be a 2D numpy array of shape (samples, features) representing EEG features.
    Output is a dictionary from predict() containing:
     {
            "label": str,
            "confidence": float,
            "probabilities": {
                "happy": float,
                "sad": float,
                "fear": float,
                "disgust": float,
                "neutral": float
            }
    """

    def __init__(
        self,
        class_labels: Optional[List[str]] = None,
        n_estimators: int = 200,
        random_state: int = 42,
    ) -> None:
        self.class_labels = class_labels or [
            "happy",
            "sad",
            "fear",
            "disgust",
            "neutral",
        ]
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=random_state,
        )
        self.is_trained = False

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        self._validate_X(X_train)
        if not isinstance(y_train, np.ndarray):
            raise TypeError("y_train must be a numpy array.")
        if len(X_train) != len(y_train):
            raise ValueError("X_train and y_train must have the same number of samples.")
        self.model.fit(X_train, y_train)
        self.is_trained = True

    def predict(self, X: np.ndarray) -> Dict[str, Any]:
        self._check_trained()
        self._validate_X(X)
        probs = self.model.predict_proba(X)
        prob_vector = probs[0]
        pred_idx = int(np.argmax(prob_vector))
        label = str(self.model.classes_[pred_idx])
        confidence = float(prob_vector[pred_idx])
        probability_map = {
            str(cls): float(prob)
            for cls, prob in zip(self.model.classes_, prob_vector)
        }
        return {
            "label": label,
            "confidence": confidence,
            "probabilities": probability_map,
        }

    def predict_batch(self, X: np.ndarray) -> List[Dict[str, Any]]:
        self._check_trained()
        self._validate_X(X)
        probs = self.model.predict_proba(X)
        results: List[Dict[str, Any]] = []
        for prob_vector in probs:
            pred_idx = int(np.argmax(prob_vector))
            label = str(self.model.classes_[pred_idx])
            confidence = float(prob_vector[pred_idx])
            probability_map = {
                str(cls): float(prob)
                for cls, prob in zip(self.model.classes_, prob_vector)
            }
            results.append(
                {
                    "label": label,
                    "confidence": confidence,
                    "probabilities": probability_map,
                }
            )
        return results

    def save(self, path: str | Path) -> None:
        payload = {
            "model": self.model,
            "class_labels": self.class_labels,
            "is_trained": self.is_trained,
        }
        joblib.dump(payload, path)

    def load(self, path: str | Path) -> None:
        payload = joblib.load(path)
        self.model = payload["model"]
        self.class_labels = payload["class_labels"]
        self.is_trained = payload["is_trained"]

    @staticmethod
    def _validate_X(X: np.ndarray) -> None:
        if not isinstance(X, np.ndarray):
            raise TypeError("X must be a numpy array.")
        if X.ndim != 2:
            raise ValueError("X must be 2D with shape (samples, features).")

    def _check_trained(self) -> None:
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call train() or load() first.")


if __name__ == "__main__":
    X_train = np.random.rand(100, 20)
    y_train = np.random.choice(
        ["happy", "sad", "fear", "disgust", "neutral"],
        size=100,
    )
    model = EmotionModel()
    model.train(X_train, y_train)
    X_test = np.random.rand(1, 20)
    print(model.predict(X_test))