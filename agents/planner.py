"""
agents/planner.py
-----------------
Planner Agent: decomposes user query into a structured task plan.

Key fix: _extract_product() no longer strips standalone numbers like 16, 15, 12.
It only removes budget numbers (those preceded by under/below/rs/inr/₹ or
large standalone numbers ≥4 digits that look like prices).
Model numbers like "16", "15 Pro", "S24" are preserved.
"""

import re
from typing import Dict, List, Optional


class PlannerAgent:

    def plan(self, user_query: str) -> Dict:
        print("[PlannerAgent] Analyzing: " + repr(user_query))

        budget  = self._extract_budget(user_query)
        product = self._extract_product(user_query, budget)
        prefs   = self._extract_preferences(user_query)
        tasks   = self._build_tasks(product, budget, prefs)

        plan = {
            "original_query": user_query,
            "product_name":   product,
            "budget_inr":     budget,
            "preferences":    prefs,
            "tasks":          tasks,
        }
        self._print_plan(plan)
        return plan

    def _extract_product(self, query: str, budget: Optional[float]) -> str:
        """
        Remove only filler words and the budget number — NOT model numbers.

        Strategy:
        1. Remove explicit budget phrases like "under 70000", "below ₹50k", "rs 60000"
        2. Remove large standalone price-like numbers (≥4 digits) ONLY if not
           directly attached to a word (e.g. "60000" alone, not "S24" or "16 Pro")
        3. Remove filler words: best, buy, cheap, affordable, etc.
        4. Leave everything else — including "16", "15 Pro Max", "S24 Ultra"
        """
        cleaned = query

        # Step 1: Remove budget phrases first (under X, below X, rs X, ₹X, X k)
        cleaned = re.sub(r'\b(under|below|around|upto|up to)\s*[₹]?\s*\d[\d,]*\s*k?\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\b(rs|inr)\.?\s*\d[\d,]*\s*k?\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[₹]\s*\d[\d,]*\s*k?\b', '', cleaned)

        # Step 2: Remove large standalone price numbers (4+ digits standing alone)
        # But NOT short numbers like 16, 15, 12, 5G, 24 which are model numbers
        cleaned = re.sub(r'(?<!\w)\d{4,}(?!\w)', '', cleaned)

        # Step 3: Remove filler words only
        filler = r'\b(best|top|buy|cheap|affordable|good|nice|latest|new|get|find|show|search|recommend|suggest|me|a|an|the|some|under|below|above|around|upto)\b'
        cleaned = re.sub(filler, '', cleaned, flags=re.IGNORECASE)

        # Step 4: Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Fallback: if we stripped everything, use original query
        return cleaned or query

    def _extract_budget(self, query: str) -> Optional[float]:
        """
        Extract budget in INR. Tries explicit patterns first, then large standalone numbers.
        Does NOT treat model numbers (2-3 digit) as budgets.
        """
        patterns = [
            # Explicit keywords — highest confidence
            (r'\b(?:under|below|around|upto|up\s+to)\s*[₹]?\s*(\d[\d,]*)\s*(k?)\b', True),
            (r'\brs\.?\s*(\d[\d,]*)\s*(k?)\b',  True),
            (r'\binr\s*(\d[\d,]*)\s*(k?)\b',     True),
            (r'[₹]\s*(\d[\d,]*)\s*(k?)\b',       True),
            # Large standalone numbers (≥4 digits) — treat as budget
            (r'(?<!\w)(\d{4,})(?!\w)\s*(k?)\b',  False),
        ]
        for pat, has_keyword in patterns:
            m = re.search(pat, query, re.IGNORECASE)
            if m:
                num = float(m.group(1).replace(',', ''))
                suffix = m.group(2).lower() if len(m.groups()) >= 2 else ''
                if suffix == 'k':
                    num *= 1000
                return num
        return None

    def _extract_preferences(self, query: str) -> List[str]:
        ql = query.lower()
        mapping = {
            "budget":         ["cheap", "budget", "affordable", "low price", "cheapest"],
            "quality":        ["best quality", "premium", "high end", "top rated", "flagship"],
            "trusted_seller": ["official", "authorized", "genuine", "authentic", "trusted"],
            "fast_delivery":  ["fast delivery", "quick", "urgent", "same day"],
        }
        found = [p for p, kws in mapping.items() if any(k in ql for k in kws)]
        return found or ["value_for_money"]

    def _build_tasks(self, product: str, budget: Optional[float], prefs: List[str]) -> List[Dict]:
        tasks = [
            {"step": 1, "agent": "SearchAgent",   "action": f"Search {repr(product)} across platforms"},
            {"step": 2, "agent": "DataProcessor", "action": "Clean and normalize listings"},
        ]
        if budget:
            tasks.append({"step": 3, "agent": "DataProcessor",
                          "action": f"Filter price <= Rs.{int(budget)}"})
        base = len(tasks) + 1
        tasks += [
            {"step": base,   "agent": "ReviewAnalyzer",     "action": "NLP sentiment analysis"},
            {"step": base+1, "agent": "FakeReviewDetector", "action": "Detect suspicious reviews"},
            {"step": base+2, "agent": "ScoringEngine",      "action": f"Compute value scores (prefs: {prefs})"},
            {"step": base+3, "agent": "CriticAgent",        "action": "Audit scores, penalize anomalies"},
            {"step": base+4, "agent": "DecisionAgent",      "action": "Generate final recommendation"},
        ]
        return tasks

    def _print_plan(self, plan: Dict):
        budget_str = f"Rs.{int(plan['budget_inr'])}" if plan['budget_inr'] else "No limit"
        print("[PlannerAgent] Plan ready:")
        print(f"  Product : {plan['product_name']}")
        print(f"  Budget  : {budget_str}")
        print(f"  Prefs   : {', '.join(plan['preferences'])}")
        for t in plan["tasks"]:
            print(f"    Step {t['step']}: [{t['agent']}] {t['action']}")