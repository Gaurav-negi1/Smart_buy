"""
start_server.py
---------------
Usage: python start_server.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))

from api.main import app
import uvicorn

if __name__ == "__main__":
    print("="*50)
    print("  SmartBuy AI — Server Starting")
    print("  API  → http://localhost:8000")
    print("  Docs → http://localhost:8000/docs")
    print("  Open frontend/index.html in browser")
    print("  Ctrl+C to stop")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
