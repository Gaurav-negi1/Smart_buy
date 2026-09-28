"""
scoring/value_score.py
-----------------------
Scoring Engine: weighted value score formula.

Default weights:
  Rating          35%
  Sentiment       20%
  Review Volume   15%
  Price Advantage 20%
  Seller Trust    10%
"""

import math
from typing import List, Dict


class ScoringEngine:

    DEFAULT_WEIGHTS = {
        "rating":          0.30,
        "sentiment":       0.18,
        "review_volume":   0.12,
        "price_advantage": 0.20,
        "seller_trust":    0.20,  # raised — stops grey market resellers topping chart
    }

    PREF_OVERRIDES = {
        "budget":         {"rating":0.22,"sentiment":0.13,"review_volume":0.10,"price_advantage":0.40,"seller_trust":0.15},
        "quality":        {"rating":0.38,"sentiment":0.27,"review_volume":0.15,"price_advantage":0.05,"seller_trust":0.15},
        "trusted_seller": {"rating":0.22,"sentiment":0.15,"review_volume":0.08,"price_advantage":0.10,"seller_trust":0.45},
    }

    def run(self, products: List[Dict], preferences: List[str] = None) -> List[Dict]:
        print(f"\n[ScoringEngine] Scoring {len(products)} products...")

        weights   = self._weights(preferences or [])
        prices    = [p["price"] for p in products if p.get("price", 0) > 0]
        avg_price = sum(prices) / len(prices) if prices else 1
        max_rev   = max((p.get("review_count", 0) for p in products), default=1)

        for p in products:
            subs  = self._subscores(p, avg_price, max_rev)
            score = sum(subs[k] * weights[k] for k in weights) * 100
            p["subscores"]    = {k: round(v * 100, 1) for k, v in subs.items()}
            p["value_score"]  = round(score, 1)
            p["weights_used"] = weights

        products.sort(key=lambda x: x["value_score"], reverse=True)

        for p in products:
            print(f"  {p.get('platform','?'):20s} | ₹{p.get('price',0):>8,.0f} | Score: {p['value_score']:5.1f}")

        print(f"[ScoringEngine] Top: {products[0].get('platform','?')} ({products[0]['value_score']}/100)")
        return products

    def _weights(self, prefs: List[str]) -> Dict:
        for p in prefs:
            if p in self.PREF_OVERRIDES:
                print(f"[ScoringEngine] Using '{p}' weight profile")
                return self.PREF_OVERRIDES[p]
        return self.DEFAULT_WEIGHTS

    def _subscores(self, p: Dict, avg_price: float, max_rev: int) -> Dict:
        # Rating score
        rating = min(p.get("rating", 3.0) / 5.0, 1.0)

        # Sentiment score (from NLP)
        sentiment = p.get("sentiment_score", 0.5)

        # Review volume (log-normalized)
        rc  = max(p.get("review_count", 0), 1)
        vol = math.log(rc + 1) / math.log(max_rev + 2)

        # Price advantage (cheaper = higher score)
        price = p.get("price", avg_price)
        price_adv = max(0, min(1, (avg_price - price) / avg_price + 0.5)) if avg_price > 0 else 0.5

        # Seller trust
        seller = (p.get("seller", "") + " " + p.get("platform", "")).lower()
        # Known grey market / unverified resellers — penalize heavily
        grey_market = ["pai international", "third party", "reseller", "grey",
                       "import", "maple store", "imagine", "apr"]
        # Known trusted official sellers — reward
        trusted = ["official", "authorized", "assured", "amazon", "flipkart",
                   "croma", "reliance digital", "vijay sales", "tata cliq",
                   "samsung shop", "apple store"]
        if any(w in seller for w in grey_market):
            trust = 0.25   # strong penalty for grey market
        elif any(w in seller for w in trusted):
            trust = 0.92
        else:
            trust = 0.60

        # Penalize fake reviews
        fake = p.get("fake_review_pct", 0)
        pen  = max(0, (fake - 20) / 100) if fake > 20 else 0

        return {
            "rating":          max(0, rating    - pen * 0.3),
            "sentiment":       max(0, sentiment - pen * 0.2),
            "review_volume":   vol,
            "price_advantage": price_adv,
            "seller_trust":    trust,
        }