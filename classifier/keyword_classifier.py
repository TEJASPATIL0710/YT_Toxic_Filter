"""
keyword_classifier.py

A simple, fully offline baseline classifier: no API key, no model
download, no network call. It scores toxicity by matching against a
small set of flagged terms and patterns.

This is NOT meant to be accurate enough for production moderation --
it exists so that:
1. The whole pipeline (fetch -> classify -> store -> display) can be
   built and tested end-to-end without waiting on API keys or model
   training.
2. It gives you a concrete, low baseline to beat once you wire up the
   Perspective API (Sprint 2) and later a fine-tuned transformer
   (Sprint 3) -- "how much better is X than a keyword list" is a good
   number to have for your portfolio write-up.

Swap this out (or run it alongside another classifier) any time --
that's the point of the shared ToxicityClassifier interface.
"""

import re

from classifier.base import ClassificationResult, ToxicityClassifier

# Deliberately mild example set -- expand this list, or better, replace
# this whole classifier with the Perspective API / a trained model once
# Sprint 2/3 are underway.
_FLAGGED_TERMS = {
    "idiot": 0.5,
    "stupid": 0.4,
    "shut up": 0.4,
    "hate you": 0.6,
    "kill yourself": 0.95,
    "kys": 0.95,
    "trash": 0.3,
    "loser": 0.4,
    "dumb": 0.3,
    "ugly": 0.3,
}

_TOXIC_THRESHOLD = 0.5


class KeywordClassifier(ToxicityClassifier):
    @property
    def name(self) -> str:
        return "keyword_baseline"

    def classify(self, text: str) -> ClassificationResult:
        lowered = text.lower()
        score = 0.0

        for term, weight in _FLAGGED_TERMS.items():
            if re.search(rf"\b{re.escape(term)}\b", lowered):
                score = max(score, weight)

        # Extra signal: ALL CAPS shouting on longer comments nudges the score up
        if len(text) > 10 and text.isupper():
            score = min(1.0, score + 0.1)

        return ClassificationResult(
            toxicity_score=round(score, 2),
            is_toxic=score >= _TOXIC_THRESHOLD,
            classifier_name=self.name,
        )
