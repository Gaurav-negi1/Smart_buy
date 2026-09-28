"""
agents/search_agent.py
----------------------
Search Agent: fetches products using the data fetcher.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict
from data.fetcher import fetch_all_products


class SearchAgent:

    def run(self, plan: Dict) -> List[Dict]:
        product = plan.get("product_name") or plan.get("original_query", "")
        budget  = plan.get("budget_inr")

        print(f"\n[SearchAgent] Searching for: '{product}'")
        products = fetch_all_products(product, budget)
        print(f"[SearchAgent] Retrieved {len(products)} listings")
        return products
