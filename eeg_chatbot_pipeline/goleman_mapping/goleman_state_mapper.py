from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class GolemanMappingResult:
    emotion: str
    confidence: Optional[float]
    goleman_domain: str
    goleman_state: str
    notes: str


class GolemanStateMapper:
    """
    Input comes from emotion_model.py
    Format looks like:
        {
            "label": "fear",
            "confidence": 0.84,
            "probabilities": {...}
        }

    Output:
        {
            "emotion": "fear",
            "confidence": 0.84,
            "goleman_domain": "self_regulation",
            "goleman_state": "stress_dysregulation",
            "notes": "high stress or anxiety state."
        }

        Note: Didn't use social awareness or relationship management domains of Goleman since those are more about interpersonal dynamics and less about internal emotional states that we can infer from EEG data.
    """

    DEFAULT_UNKNOWN = {
        "goleman_domain": "self_awareness",
        "goleman_state": "unclassified_emotional_state",
        "notes": "Emotion could not be mapped to a known Goleman-style state.",
    }

    EMOTION_TO_GOLEMAN: Dict[str, Dict[str, str]] = {
        "happy": {
            "goleman_domain": "motivation",
            "goleman_state": "positive_engagement",
            "notes": "positive, energized state",
        },
        "neutral": {
            "goleman_domain": "self_regulation",
            "goleman_state": "regulated_baseline",
            "notes": "stable, neutral state",
        },
        "sad": {
            "goleman_domain": "self_awareness",
            "goleman_state": "low_mood_awareness",
            "notes": "low energy, negative state",
        },

        "fear": {
            "goleman_domain": "self_regulation",
            "goleman_state": "stress_dysregulation",
            "notes": "high stress or anxiety state",
        },
        "disgust": {
            "goleman_domain": "self_awareness",
            "goleman_state": "aversive_reactivity",
            "notes": "strong discomfort or rejection",
        },
    }

    def map(self, emotion_payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(emotion_payload, dict):
            raise TypeError("emotion_payload needs to be a dictionary.")

        raw_emotion = emotion_payload.get("emotion", emotion_payload.get("label"))
        confidence = emotion_payload.get("confidence")

        if raw_emotion is None:
            raise ValueError("emotion_payload should include 'emotion' or 'label'.")

        emotion = self._normalize_emotion(raw_emotion)
        mapped = self.EMOTION_TO_GOLEMAN.get(emotion, self.DEFAULT_UNKNOWN)

        result = GolemanMappingResult(
            emotion=emotion,
            confidence=self._coerce_confidence(confidence),
            goleman_domain=mapped["goleman_domain"],
            goleman_state=mapped["goleman_state"],
            notes=mapped["notes"],
        )
        return self._to_dict(result)

    @staticmethod
    def _normalize_emotion(emotion: Any) -> str:
        if not isinstance(emotion, str):
            raise TypeError("Emotion label needs to be a string.")
        return emotion.strip().lower()

    @staticmethod
    def _coerce_confidence(confidence: Any) -> Optional[float]:
        if confidence is None:
            return None
        try:
            value = float(confidence)
        except (TypeError, ValueError) as exc:
            raise TypeError("Confidence should be numeric.") from exc
        if not 0.0 <= value <= 1.0:
            raise ValueError("Confidence needs to be between 0.0 and 1.0.")
        return value

    @staticmethod
    def _to_dict(result: GolemanMappingResult) -> Dict[str, Any]:
        return {
            "emotion": result.emotion,
            "confidence": result.confidence,
            "goleman_domain": result.goleman_domain,
            "goleman_state": result.goleman_state,
            "notes": result.notes,
        }


if __name__ == "__main__":
    mapper = GolemanStateMapper()
    #for testing
    example_inputs = [
        {"label": "fear", "confidence": 0.84},
        {"label": "happy", "confidence": 0.91},
        {"label": "neutral"},
        {"label": "sad", "confidence": 0.63},
    ]
    for payload in example_inputs:
        print(mapper.map(payload))