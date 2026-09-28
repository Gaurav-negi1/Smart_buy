"""
api/main.py
-----------
FastAPI backend for SmartBuy AI.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from agents.pipeline   import SmartBuyPipeline
from database.models   import init_db, Session, SearchLog

app = FastAPI(title="SmartBuy AI", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()
pipeline = SmartBuyPipeline()


class SearchRequest(BaseModel):
    query:  str
    budget: Optional[float] = None


@app.get("/")
def root():
    return {"message": "SmartBuy AI running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search(req: SearchRequest):
    q = req.query.strip()
    if not q:
        raise HTTPException(400, "Query cannot be empty")
    try:
        if req.budget and "under" not in q.lower():
            q = f"{q} under {int(float(req.budget))}"
        result = pipeline.run(q)
        if "error" in result:
            raise HTTPException(500, result["error"])
        _log(result)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        print(f"[API] ValueError: {e}")
        raise HTTPException(500, f"Data parsing error: {e} — try a more specific query")
    except Exception as e:
        import traceback
        print(f"[API] Unhandled error:\n{traceback.format_exc()}")
        raise HTTPException(500, f"Pipeline error: {e}")

@app.get("/history")
def history(limit: int = 10):
    db = Session()
    try:
        rows = db.query(SearchLog).order_by(SearchLog.created_at.desc()).limit(limit).all()
        return [{"query": r.query, "best_platform": r.best_platform,
                 "best_score": r.best_score, "created_at": str(r.created_at)} for r in rows]
    finally:
        db.close()

def _log(result: dict):
    db = Session()
    try:
        db.add(SearchLog(
            query         = result.get("query", ""),
            best_platform = result.get("recommended_platform", ""),
            best_score    = result.get("value_score", 0),
            result_count  = len(result.get("all_products", [])),
        ))
        db.commit()
    except Exception as e:
        print(f"[DB] {e}")
    finally:
        db.close()