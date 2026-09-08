"""
base.py (classifier)

Every classifier (keyword baseline, Perspective API, future custom
transformer) implements this same interface, so the pipeline can swap
between them -- or run several side by side -- without changing any
other code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    toxicity_score: float  # 0.0 (not toxic) to 1.0 (highly toxic)
    is_toxic: bool
    classifier_name: str


class ToxicityClassifier(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier stored alongside scores, e.g. 'keyword_baseline'."""
        raise NotImplementedError

    @abstractmethod
    def classify(self, text: str) -> ClassificationResult:
        raise NotImplementedError
