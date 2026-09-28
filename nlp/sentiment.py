"""
nlp/sentiment.py
----------------
Sentiment analysis using TextBlob (with keyword fallback).
Runs 100% locally — no API calls.
"""

import re
from typing import List, Dict

try:
    from textblob import TextBlob
    TEXTBLOB_OK = True
except ImportError:
    TEXTBLOB_OK = False


class SentimentAnalyzer:

    POSITIVE = {
        "excellent","amazing","great","perfect","outstanding","superb",
        "fantastic","wonderful","love","best","awesome","brilliant",
        "recommend","satisfied","happy","quality","worth","good",
        "fast","smooth","reliable","genuine","solid","flawless",
    }
    NEGATIVE = {
        "terrible","awful","poor","bad","horrible","worst","broken",
        "fake","disappointing","useless","waste","damaged","slow",
        "defective","returned","refund","misleading","fraud",
        "flimsy","unreliable","regret","avoid","stopped","cheap",
    }

    def analyze(self, reviews: List[str]) -> Dict:
        if not reviews:
            return {"score": 0.5, "label": "Neutral", "positive": 0, "negative": 0, "total": 0}

        scores, pos, neg = [], 0, 0
        for r in reviews:
            s = self._score(r)
            scores.append(s)
            if s > 0.55:   pos += 1
            elif s < 0.45: neg += 1

        avg = sum(scores) / len(scores)
        return {
            "score":    round(avg, 4),
            "label":    self._label(avg),
            "positive": pos,
            "negative": neg,
            "neutral":  len(reviews) - pos - neg,
            "total":    len(reviews),
        }

    def _score(self, text: str) -> float:
        if TEXTBLOB_OK:
            try:
                return (TextBlob(text).sentiment.polarity + 1) / 2
            except Exception:
                pass
        words = set(re.findall(r'\b\w+\b', text.lower()))
        p = len(words & self.POSITIVE)
        n = len(words & self.NEGATIVE)
        return p / (p + n) if (p + n) > 0 else 0.5

    def _label(self, s: float) -> str:
        if s >= 0.70: return "Very Positive"
        if s >= 0.55: return "Positive"
        if s >= 0.45: return "Neutral"
        if s >= 0.30: return "Negative"
        return "Very Negative"
