"""
run_cli.py
----------
Usage: python run_cli.py "Samsung Galaxy under 60000"
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.pipeline import SmartBuyPipeline

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter query: ").strip()
    if not query:
        query = "Samsung smartphone under 50000"
    result = SmartBuyPipeline().run(query)
    if "error" not in result:
        print(f"\nBest: {result['recommended_platform']} | Score: {result['value_score']}/100")
