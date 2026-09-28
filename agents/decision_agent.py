"""
agents/decision_agent.py
-------------------------
Decision Agent: selects the best product and generates a
human-readable recommendation with clickable product links.
"""

from typing import List, Dict


class DecisionAgent:

    def run(self, products: List[Dict], plan: Dict) -> Dict:
        print(f"\n[DecisionAgent] Generating recommendation...")

        if not products:
            return {"error": "No products available", "query": plan.get("original_query", "")}

        best      = products[0]
        runner_up = products[1] if len(products) > 1 else None
        risk      = self._risk(best)

        rec = {
            "query":                plan.get("original_query", ""),
            "recommended_platform": best.get("platform", "Unknown"),
            "product_name":         best.get("name", "Unknown"),
            "price":                best.get("price", 0),
            "rating":               best.get("rating", 0),
            "review_count":         best.get("review_count", 0),
            "value_score":          best.get("value_score", 0),
            "risk_level":           risk,
            "sentiment_label":      best.get("sentiment", {}).get("label", "N/A"),
            "fake_review_pct":      best.get("fake_review_pct", 0),
            "product_url":          best.get("product_url", best.get("link", "")),
            "affiliate_link":       best.get("affiliate_link", ""),
            "reason":               self._reason(best, runner_up, plan),
            "pros":                 self._pros(best),
            "warnings":             best.get("audit", {}).get("issues", []),
            "subscores":            best.get("subscores", {}),
            "alternatives":         self._alts(products[1:4]),
            "all_products":         self._all(products),
        }

        self._print(rec)
        return rec

    def _risk(self, p: Dict) -> str:
        fake   = p.get("fake_review_pct", 0)
        issues = len(p.get("audit", {}).get("issues", []))
        score  = p.get("value_score", 0)
        if fake > 40 or issues >= 3:           return "High"
        if fake > 20 or issues >= 1 or score < 55: return "Medium"
        return "Low"

    def _reason(self, best: Dict, runner_up, plan: Dict) -> str:
        parts = [f"Top value score of {best['value_score']}/100"]
        if best.get("rating", 0) >= 4.3:
            parts.append(f"strong rating {best['rating']}/5")
        if best.get("review_count", 0) > 200:
            parts.append(f"large review base ({best['review_count']} reviews)")
        label = best.get("sentiment", {}).get("label", "")
        if "Positive" in label:
            parts.append(f"{label.lower()} review sentiment")
        if best.get("fake_review_pct", 0) < 15:
            parts.append("low fake-review risk")
        if runner_up:
            diff = best["value_score"] - runner_up.get("value_score", 0)
            if diff > 5:
                parts.append(f"outperforms next option by {diff:.1f} pts")
        budget = plan.get("budget_inr")
        if budget and best.get("price", 0) <= budget:
            parts.append(f"within ₹{budget:,.0f} budget")
        return ". ".join(p.capitalize() for p in parts) + "."

    def _pros(self, p: Dict) -> List[str]:
        pros = []
        if p.get("rating", 0) >= 4.3:         pros.append(f"High rating: {p['rating']}/5")
        if p.get("review_count", 0) > 100:     pros.append(f"{p['review_count']}+ reviews")
        if p.get("fake_review_pct", 0) < 15:   pros.append("Authentic reviews")
        label = p.get("sentiment", {}).get("label", "")
        if "Positive" in label:                pros.append(label + " sentiment")
        ss = p.get("subscores", {})
        if ss.get("price_advantage", 0) > 60:  pros.append("Good price vs market")
        return pros[:4]

    def _alts(self, products: List[Dict]) -> List[Dict]:
        return [{
            "platform": p["platform"], 
            "name": p.get("name", "")[:40],
            "price": p["price"],
            "value_score": p["value_score"], 
            "rating": p["rating"],
            "product_url": p.get("product_url", p.get("link", ""))
        } for p in products]

    def _all(self, products: List[Dict]) -> List[Dict]:
        return [{
            "rank": i+1, 
            "platform": p["platform"],
            "seller_label": p.get("seller_label", p.get("seller", "")),
            "name": p["name"], 
            "price": p["price"], 
            "rating": p["rating"],
            "review_count": p["review_count"], 
            "value_score": p["value_score"],
            "risk": self._risk(p), 
            "sentiment": p.get("sentiment", {}).get("label", "N/A"),
            "fake_pct": p.get("fake_review_pct", 0),
            "product_url": p.get("product_url", p.get("link", "")),
            "seller_trust": p.get("seller_trust", {}).get("classification", "N/A")
        } for i, p in enumerate(products)]

    def _print(self, rec: Dict):
        print("\n" + "="*60)
        print("  SMARTBUY AI — RECOMMENDATION")
        print("="*60)
        print(f"  Platform  : {rec['recommended_platform']}")
        print(f"  Product   : {rec['product_name'][:55]}")
        print(f"  Price     : ₹{rec['price']:,.0f}")
        print(f"  Rating    : {rec['rating']}/5")
        print(f"  Score     : {rec['value_score']}/100")
        print(f"  Risk      : {rec['risk_level']}")
        print(f"  Sentiment : {rec['sentiment_label']}")
        print(f"  Link      : {rec.get('product_url', 'N/A')[:60]}...")
        print(f"  Reason    : {rec['reason'][:100]}")
        if rec["warnings"]:
            print(f"  Warnings  : {'; '.join(rec['warnings'])}")
        print("="*60)