"""
agents/pipeline.py
------------------
Master Pipeline: orchestrates all agents in order.
  Planner → Search → Analysis → Scoring → Critic → Decision
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict
from agents.planner        import PlannerAgent
from agents.search_agent   import SearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.critic_agent   import CriticAgent
from agents.decision_agent import DecisionAgent
from scoring.value_score   import ScoringEngine


class SmartBuyPipeline:

    def __init__(self):
        self.planner  = PlannerAgent()
        self.search   = SearchAgent()
        self.analysis = AnalysisAgent()
        self.scoring  = ScoringEngine()
        self.critic   = CriticAgent()
        self.decision = DecisionAgent()

    def run(self, user_query: str) -> Dict:
        t0 = time.time()
        print("\n" + "="*60)
        print("  SMARTBUY AI — PIPELINE STARTED")
        print("="*60)
        print(f"  Query: {user_query}")

        try:
            plan     = self.planner.plan(user_query)
            products = self.search.run(plan)

            if not products:
                return {"error": "No products found.", "query": user_query}

            products = self.analysis.run(products)
            products = self.scoring.run(products, plan.get("preferences", []))
            products = self.critic.run(products)
            result   = self.decision.run(products, plan)
            result["execution_time_sec"] = round(time.time() - t0, 2)
            print(f"\n[Pipeline] Done in {result['execution_time_sec']}s")
            return result

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e), "query": user_query}
