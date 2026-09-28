"""
data/mock_fetcher.py
Generates realistic mock product data when SerpAPI is unavailable.
Also tries FakeStoreAPI and DummyJSON (free, no key needed).
"""

import requests
import random
import re
from typing import List, Dict


POSITIVE_REVIEWS = [
    "Excellent product! Works perfectly and great build quality.",
    "Very happy with this purchase. Highly recommend to everyone.",
    "Amazing value for money. Fast delivery and good packaging.",
    "Best product in this category. Totally worth every rupee.",
    "Superb quality! Using it daily and it works flawlessly.",
    "Great product, exactly as described. Very satisfied customer.",
    "Outstanding performance. Would definitely buy again.",
    "Solid build, great features. Exceeded my expectations.",
]
NEGATIVE_REVIEWS = [
    "Disappointed with quality. Not worth the price at all.",
    "Stopped working after two weeks. Very poor build quality.",
    "Delivery was late and packaging was damaged on arrival.",
    "Product looks nothing like the pictures. Misleading listing.",
    "Bad experience overall. Customer service was unhelpful.",
    "Felt very cheap. Not durable at all for daily use.",
]
MIXED_REVIEWS = [
    "Decent product for the price. Has some minor issues.",
    "Good overall but delivery took longer than expected.",
    "Works fine but quality could be better for the price.",
    "Average product. Nothing special but gets the job done.",
    "Okay for occasional use but not for daily heavy use.",
    "Looks good but battery life is not as advertised.",
]
SUSPICIOUS_REVIEWS = [
    "Best product ever!!!",
    "Amazing!!!",
    "Perfect 10/10!!!",
    "Best best best!!!",
    "Love it love it!!!",
]


def generate_reviews(rating: float) -> List[str]:
    if rating >= 4.2:
        pool = random.sample(POSITIVE_REVIEWS, min(4, len(POSITIVE_REVIEWS))) + \
               random.sample(MIXED_REVIEWS, 2)
    elif rating >= 3.5:
        pool = random.sample(MIXED_REVIEWS, 3) + \
               random.sample(POSITIVE_REVIEWS, 2) + \
               random.sample(NEGATIVE_REVIEWS, 1)
    else:
        pool = random.sample(NEGATIVE_REVIEWS, 3) + \
               random.sample(MIXED_REVIEWS, 2) + \
               random.sample(POSITIVE_REVIEWS, 1)
    if random.random() < 0.3:
        pool += random.sample(SUSPICIOUS_REVIEWS, 2)
    random.shuffle(pool)
    return pool


def fetch_fakestore(query: str) -> List[Dict]:
    try:
        resp = requests.get("https://fakestoreapi.com/products", timeout=6)
        if resp.status_code == 200:
            all_p = resp.json()
            q = query.lower()
            matched = [p for p in all_p if q in p.get("title","").lower() or q in p.get("category","").lower()]
            if not matched:
                matched = all_p[:5]
            results = []
            for p in matched[:4]:
                rd = p.get("rating", {})
                rating = float(rd.get("rate", 3.5))
                results.append({
                    "name":         p.get("title", "Unknown"),
                    "platform":     "ShopEasy",
                    "price":        round(p.get("price", 0) * 83, 2),
                    "rating":       rating,
                    "review_count": _safe_int(rd.get("count", 50)),
                    "seller":       "ShopEasy Official",
                    "reviews":      generate_reviews(rating),
                    "source":       "fakestore_api",
                })
            return results
    except Exception:
        pass
    return []


def fetch_dummyjson(query: str) -> List[Dict]:
    try:
        resp = requests.get(
            "https://dummyjson.com/products/search",
            params={"q": query, "limit": 5},
            timeout=6
        )
        if resp.status_code == 200:
            products = resp.json().get("products", [])
            results = []
            for p in products[:4]:
                rating = float(p.get("rating", 3.5))
                results.append({
                    "name":         p.get("title", "Unknown"),
                    "platform":     "QuickMart",
                    "price":        round(p.get("price", 0) * 83, 2),
                    "rating":       rating,
                    "review_count": random.randint(40, 800),
                    "seller":       "QuickMart Authorized",
                    "reviews":      generate_reviews(rating),
                    "source":       "dummyjson_api",
                })
            return results
    except Exception:
        pass
    return []


def get_mock_products(query: str) -> List[Dict]:
    """Full mock product set — always works offline."""
    base = random.randint(15000, 80000)
    return [
        {
            "name": f"{query} - Premium Edition",
            "platform": "Amazon",
            "price": base,
            "rating": round(random.uniform(3.8, 4.7), 1),
            "review_count": random.randint(200, 5000),
            "seller": "Amazon Official",
            "reviews": generate_reviews(4.3),
            "source": "mock",
        },
        {
            "name": f"{query} - Standard Pack",
            "platform": "Flipkart",
            "price": base - random.randint(500, 3000),
            "rating": round(random.uniform(3.5, 4.5), 1),
            "review_count": random.randint(100, 3000),
            "seller": "Flipkart Assured",
            "reviews": generate_reviews(3.9),
            "source": "mock",
        },
        {
            "name": f"{query} - Value Buy",
            "platform": "Croma",
            "price": base - random.randint(1000, 5000),
            "rating": round(random.uniform(3.0, 4.6), 1),
            "review_count": random.randint(20, 300),
            "seller": "Croma Retail",
            "reviews": generate_reviews(3.6),
            "source": "mock",
        },
        {
            "name": f"{query} - Bundle Offer",
            "platform": "Reliance Digital",
            "price": base + random.randint(200, 2000),
            "rating": round(random.uniform(4.0, 4.9), 1),
            "review_count": random.randint(500, 8000),
            "seller": "Reliance Official",
            "reviews": generate_reviews(4.6),
            "source": "mock",
        },
        {
            "name": f"{query} - Grey Import",
            "platform": "ShopClues",
            "price": base - random.randint(3000, 10000),
            "rating": round(random.uniform(2.5, 4.0), 1),
            "review_count": random.randint(5, 60),
            "seller": "Grey Market Reseller",
            "reviews": generate_reviews(2.8),
            "source": "mock",
        },
    ]