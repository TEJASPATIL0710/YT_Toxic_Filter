"""
perspective_classifier.py

Wraps Google's Perspective API (https://perspectiveapi.com/) for
toxicity scoring. This requires its own API key (separate from your
YouTube Data API key) -- get one at:
https://developers.perspectiveapi.com/s/docs-get-started

Set it as an environment variable:
    export PERSPECTIVE_API_KEY="your-key-here"

This classifier makes a real network call per comment, so it's not
used by default (KeywordClassifier is the zero-setup fallback) -- but
once you have a key, this is a much stronger baseline than the keyword
list, and a good comparison point for Sprint 3's custom model.
"""

import os

import requests

from classifier.base import ClassificationResult, ToxicityClassifier

_ENDPOINT = (
    "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
)
_TOXIC_THRESHOLD = 0.5


class PerspectiveClassifier(ToxicityClassifier):
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("PERSPECTIVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No Perspective API key found. Pass api_key= or set "
                "PERSPECTIVE_API_KEY."
            )

    @property
    def name(self) -> str:
        return "perspective"

    def classify(self, text: str) -> ClassificationResult:
        response = requests.post(
            _ENDPOINT,
            params={"key": self.api_key},
            json={
                "comment": {"text": text},
                "requestedAttributes": {"TOXICITY": {}},
                "languages": ["en"],
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        score = data["attributeScores"]["TOXICITY"]["summaryScore"]["value"]

        return ClassificationResult(
            toxicity_score=round(score, 3),
            is_toxic=score >= _TOXIC_THRESHOLD,
            classifier_name=self.name,
        )
