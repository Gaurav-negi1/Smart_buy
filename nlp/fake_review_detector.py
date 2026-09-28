"""
nlp/fake_review_detector.py
----------------------------
Detects suspicious reviews using heuristic rules. Fully offline.
"""

import re
from typing import List, Dict
from collections import Counter


class FakeReviewDetector:

    GENERIC_PHRASES = [
        "best product", "love it", "highly recommend", "must buy",
        "great value", "perfect product", "amazing product", "best ever",
        "five stars", "10/10",
    ]

    def analyze(self, reviews: List[str]) -> Dict:
        if not reviews:
            return {"fake_pct": 0.0, "flags": [], "risk": "Unknown", "suspicious_count": 0}

        suspicious, flags = 0, []
        for r in reviews:
            f = self._check_single(r)
            if f:
                suspicious += 1
                flags.extend(f)

        cross = self._check_cross(reviews)
        flags.extend(cross)
        if cross:
            suspicious += len(cross)

        fake_pct = round((suspicious / len(reviews)) * 100, 1)
        return {
            "fake_pct":        fake_pct,
            "suspicious_count": suspicious,
            "total_reviews":   len(reviews),
            "flags":           list(set(flags))[:5],
            "risk":            self._risk(fake_pct),
        }

    def _check_single(self, review: str) -> List[str]:
        flags = []
        words = review.split()

        if len(words) < 4:
            flags.append("Extremely short review")
        if review.count("!") >= 3:
            flags.append("Excessive exclamation marks")
        if review.isupper() and len(review) > 5:
            flags.append("All-caps review")

        rl = review.lower()
        for phrase in self.GENERIC_PHRASES:
            if phrase in rl and len(words) < 8:
                flags.append(f"Generic filler phrase: '{phrase}'")
                break

        return flags

    def _check_cross(self, reviews: List[str]) -> List[str]:
        flags = []
        norm = [re.sub(r"\s+", " ", r.lower().strip()) for r in reviews]

        if any(c > 1 for c in Counter(norm).values()):
            flags.append("Duplicate reviews detected")
        if sum(1 for r in reviews if len(r.split()) < 6) / len(reviews) > 0.5:
            flags.append("Majority of reviews suspiciously short")
        if sum(1 for r in reviews if "!" in r) / len(reviews) > 0.6:
            flags.append("Unusually high rate of excited reviews")

        return flags

    def _risk(self, pct: float) -> str:
        if pct < 15:  return "Low"
        if pct < 35:  return "Medium"
        if pct < 60:  return "High"
        return "Very High"
