"""
agents/analysis_agent.py
-------------------------
Analysis Agent: runs NLP on all product reviews.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict
from nlp.sentiment import SentimentAnalyzer
from nlp.fake_review_detector import FakeReviewDetector


class AnalysisAgent:

    def __init__(self):
        self.sentiment = SentimentAnalyzer()
        self.fake      = FakeReviewDetector()

    def run(self, products: List[Dict]) -> List[Dict]:
        print(f"\n[AnalysisAgent] Analyzing reviews for {len(products)} products...")

        for i, p in enumerate(products):
            reviews = p.get("reviews", [])
            sr = self.sentiment.analyze(reviews)
            fr = self.fake.analyze(reviews)

            p["sentiment"]        = sr
            p["sentiment_score"]  = sr["score"]
            p["fake_analysis"]    = fr
            p["fake_review_pct"]  = fr["fake_pct"]

            print(f"  [{i+1}/{len(products)}] {p.get('platform','?'):20s} | "
                  f"Sentiment: {sr['label']:15s} | Fake: {fr['fake_pct']}%")

        print("[AnalysisAgent] NLP complete")
        return products
