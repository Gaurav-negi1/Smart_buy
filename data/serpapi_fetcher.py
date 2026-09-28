"""
data/serpapi_fetcher.py
Fetches REAL product listings from Google Shopping via SerpAPI.
Free tier: 100 searches/month — https://serpapi.com
"""

import requests
from typing import List, Dict
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SERPAPI_KEY


SERPAPI_URL = "https://serpapi.com/search"


def fetch_google_shopping(query: str, budget: float = None) -> List[Dict]:
    """
    Fetch real product listings from Google Shopping.
    Returns normalized product dicts.
    """
    if not SERPAPI_KEY or SERPAPI_KEY == "your_serpapi_key_here":
        print("[SerpAPI] ⚠ No API key set. Add SERPAPI_KEY to .env file.")
        return []

    params = {
        "engine": "google_shopping",
        "q": query,
        "api_key": SERPAPI_KEY,
        "gl": "in",          # India
        "hl": "en",
        "num": 10,
    }

    try:
        print(f"[SerpAPI] 🌐 Fetching real Google Shopping results for: '{query}'")
        resp = requests.get(SERPAPI_URL, params=params, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("shopping_results", [])
        if not results:
            print("[SerpAPI] No shopping results returned.")
            return []

        products = []
        for item in results[:8]:
            price = _parse_price(item.get("price", "0"))
            if budget and price > budget * 1.05:
                continue

            products.append({
                "name":         item.get("title", "Unknown Product"),
                "platform":     _extract_platform(item.get("source", "Online Store")),
                "price":        price,
                "rating":       float(item.get("rating", 0) or 3.5),
                "review_count": _safe_int(item.get("reviews", 0)),
                "seller":       item.get("source", "Unknown Seller"),
                "link":         item.get("link", ""),
                "thumbnail":    item.get("thumbnail", ""),
                "reviews":      [],   # SerpAPI doesn't return review text
                "source":       "google_shopping",
            })

        print(f"[SerpAPI] ✅ Got {len(products)} real listings")
        return products

    except requests.exceptions.HTTPError as e:
        if "401" in str(e):
            print("[SerpAPI] ❌ Invalid API key. Check your .env file.")
        elif "429" in str(e):
            print("[SerpAPI] ❌ Rate limit hit. Free tier = 100/month.")
        else:
            print(f"[SerpAPI] ❌ HTTP error: {e}")
    except Exception as e:
        print(f"[SerpAPI] ❌ Error: {e}")

    return []


def _parse_price(price_str: str) -> float:
    """Parse price string like '₹59,999' or '$649' → float."""
    import re
    cleaned = re.sub(r'[^\d.]', '', str(price_str))
    try:
        val = float(cleaned)
        # If price looks like USD (< 5000), convert to INR approx
        if val < 5000 and val > 0:
            val = val * 83
        return round(val, 2)
    except Exception:
        return 0.0


def _extract_platform(source: str) -> str:
    """
    Map SerpAPI source string to a clean platform name.
    Known stores get a canonical name.
    Unknown stores are cleaned up automatically.
    """
    import re
    KNOWN = {
        "amazon":       "Amazon",
        "flipkart":     "Flipkart",
        "croma":        "Croma",
        "reliance":     "Reliance Digital",
        "vijay":        "Vijay Sales",
        "tatacliq":     "Tata Cliq",
        "tata cliq":    "Tata Cliq",
        "myntra":       "Myntra",
        "meesho":       "Meesho",
        "snapdeal":     "Snapdeal",
        "paytm":        "Paytm Mall",
        "jio":          "JioMart",
        "samsung":      "Samsung",
        "apple":        "Apple",
        "oneplus":      "OnePlus",
        "xiaomi":       "Mi Store",
        "mi.com":       "Mi Store",
        "pai":          "Pai International",
        "maple":        "Maple Store",
        "imagine":      "Imagine (APR)",
        "poorvika":     "Poorvika",
        "sangeetha":    "Sangeetha",
        "istore":       "iStore",
        "indiamart":    "IndiaMart",
        "shopclues":    "ShopClues",
        "infibeam":     "Infibeam",
        "tataneo":      "Tata Neu",
        "cashify":      "Cashify",
        "smartprix":    "SmartPrix",
        "91mobiles":    "91Mobiles",
    }
    sl = source.lower().strip()
    for key, name in KNOWN.items():
        if key in sl:
            return name
    # Unknown — clean up domain/url style names automatically
    cleaned = re.sub(r'\.(com|in|co\.in|net|org|store|shop)(\/.*)?$', '', sl, flags=re.IGNORECASE)
    cleaned = re.sub(r'^www\.', '', cleaned)
    cleaned = ' '.join(w.capitalize() for w in cleaned.replace('-', ' ').replace('_', ' ').split())
    return cleaned if cleaned else "Online Store"