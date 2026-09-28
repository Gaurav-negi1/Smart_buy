"""
agents/critic_agent.py
-----------------------
Critic Agent: audits scores and applies penalties/bonuses.
This is the self-reflection loop that makes the system truly agentic.

Checks:
  1. High rating + very few reviews       → penalty 12
  2. Sentiment contradicts star rating    → penalty 10
  3. High fake review %                   → penalty up to 25
  4. Price suspiciously below market      → penalty  8
  5. Unauthorized / grey market seller    → penalty 15
  6. High trust signals                   → bonus    5
"""

from typing import List, Dict, Tuple


class CriticAgent:

    FAKE_THRESHOLD      = 35.0   # % above which to penalise
    LOW_REVIEW_COUNT    = 15     # fewer = untrustworthy rating
    SENTIMENT_GAP       = 0.25   # max allowed gap
    PRICE_DROP_LIMIT    = 0.40   # >40% below avg = suspicious

    def run(self, products: List[Dict]) -> List[Dict]:
        print(f"\n[CriticAgent] Auditing {len(products)} products...")

        prices    = [p.get("price", 0) for p in products]
        avg_price = sum(prices) / len(prices) if prices else 1

        for p in products:
            issues, adjustments = self._audit(p, avg_price)
            orig    = p["value_score"]
            penalty = sum(a.get("penalty", 0) for a in adjustments)
            bonus   = sum(a.get("bonus",   0) for a in adjustments)
            final   = round(max(0, min(100, orig - penalty + bonus)), 1)

            p["audit"] = {
                "issues":         issues,
                "adjustments":    adjustments,
                "original_score": orig,
                "penalty":        penalty,
                "bonus":          bonus,
                "final_score":    final,
            }
            p["value_score"] = final

            tag = "⚠ " if issues else "✅"
            print(f"  {tag} {p.get('platform','?'):20s} | {orig} → {final}"
                  + (f" | {issues[0]}" if issues else ""))

        products.sort(key=lambda x: x["value_score"], reverse=True)
        print("[CriticAgent] Audit complete")
        return products

    def _audit(self, p: Dict, avg_price: float) -> Tuple[List, List]:
        issues, adj = [], []

        rating  = p.get("rating", 3.0)
        rc      = p.get("review_count", 0)
        sent    = p.get("sentiment_score", 0.5)
        fake    = p.get("fake_review_pct", 0)
        price   = p.get("price", avg_price)
        seller  = (p.get("seller", "") + p.get("platform", "")).lower()

        # 1. High rating, very few reviews
        if rating >= 4.5 and rc < self.LOW_REVIEW_COUNT:
            issues.append("High rating but very few reviews")
            adj.append({"reason": "Unverified rating", "penalty": 12})

        # 2. Sentiment vs star mismatch
        if abs(rating / 5.0 - sent) > self.SENTIMENT_GAP:
            issues.append("Review text contradicts star rating")
            adj.append({"reason": "Sentiment/rating mismatch", "penalty": 10})

        # 3. Fake review rate
        if fake > self.FAKE_THRESHOLD:
            issues.append(f"High fake review rate ({fake:.0f}%)")
            adj.append({"reason": "Fake reviews", "penalty": min(25, int(fake / 2))})

        # 4. Price too far below market
        if avg_price > 0 and (avg_price - price) / avg_price > self.PRICE_DROP_LIMIT:
            issues.append("Price suspiciously below market average")
            adj.append({"reason": "Suspiciously low price", "penalty": 8})

        # 5. Unauthorised seller
        grey_list = ["third party", "reseller", "grey", "pai international", "maple store", "imagine", "apr"]
        if any(w in seller for w in grey_list):
            issues.append("Unauthorised / grey market seller")
            adj.append({"reason": "Unauthorised seller", "penalty": 15})

        # 6. Trust bonus
        if rc > 500 and sent > 0.65 and fake < 15:
            adj.append({"reason": "High trust: volume + sentiment + low fake rate", "bonus": 5})

        return issues, adj