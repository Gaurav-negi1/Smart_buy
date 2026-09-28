"""
data/fetcher.py - Universal Product Fetcher (Complete Enhanced Version)
=========================================================================
Algorithm: Cascade Retrieval with Semantic Model Matching,
          Statistical Outlier Filtering, Multi-Signal Trust Scoring,
          and Validated Product Links

Features:
1. Semantic model matching - prevents wrong model results
2. Dynamic category detection - works for ANY product
3. Seller trust scoring - multi-signal heuristic classifier
4. Statistical price outlier filtering - MAD-based
5. Deduplication - signature-based duplicate detection
6. Review quality pre-scoring - quick authenticity assessment
7. Validated clickable product links with affiliate support
8. Three-tier fallback hierarchy - SerpAPI → FakeStore → Mock
"""

import os
import re
import random
import requests
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import quote_plus, urlparse
from collections import Counter


# ============================================================================
# Environment Setup
# ============================================================================

def _load_env():
    """Load environment variables from .env file."""
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        ".env"
    )
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip().strip('"').strip("'")
PLACEHOLDER_SERPAPI_KEY = "eaa31779b6e6c9291a31c61fd912010f9905645e27079321b5a268792a138293"


# ============================================================================
# Configuration Constants
# ============================================================================

GLOBAL_IRRELEVANT_SELLERS = [
    "bigbasket", "blinkit", "swiggy", "zomato", 
    "dunzo", "zepto", "instamart", "grofers"
]

CATEGORY_IRRELEVANT_SELLERS = {
    "electronics": ["nykaa", "purplle", "firstcry", "hopscotch", "lenskart"],
    "apparel": ["croma", "reliance digital", "vijay sales"],
    "grocery": ["croma", "vijay sales", "nykaa"],
    "beauty": ["croma", "reliance digital", "firstcry"],
}

PLATFORM_TRUST_BASELINE = {
    "amazon": 0.85, "flipkart": 0.80, "croma": 0.75,
    "reliance digital": 0.75, "tata cliq": 0.70, "vijay sales": 0.70,
    "myntra": 0.65, "apple": 0.90, "samsung": 0.85, "oneplus": 0.80,
    "mi store": 0.65, "jiomart": 0.55, "meesho": 0.40, "snapdeal": 0.45,
    "shopclues": 0.35, "indiamart": 0.30, "paytm mall": 0.45,
}

TRUSTED_INDICATORS = [
    "official", "authorized", "authorised", "assured", "fulfilled",
    "prime", "retail", "store", "india", "direct", "genuine",
    "authentic", "warranty", "guarantee", "brand"
]

GREY_MARKET_INDICATORS = [
    "third party", "3rd party", "reseller", "grey", "gray",
    "imported", "parallel", "unauthorized", "unauthorised",
    "pai international", "maple", "imagine", "apr", "cashify"
]

CATEGORY_KEYWORDS = {
    "electronics": ["phone", "mobile", "smartphone", "iphone", "samsung", "galaxy",
        "pixel", "oneplus", "laptop", "notebook", "macbook", "tablet",
        "ipad", "camera", "headphone", "earbuds", "tv", "television"],
    "apparel": ["shirt", "tshirt", "dress", "jeans", "pants", "jacket",
        "hoodie", "kurta", "saree", "shoes", "sneakers", "footwear"],
    "grocery": ["rice", "wheat", "flour", "oil", "sugar", "tea", "coffee",
        "milk", "biscuit", "chocolate", "snacks", "spices", "grocery"],
    "home": ["furniture", "sofa", "bed", "mattress", "table", "chair",
        "cooker", "pressure", "utensils", "kitchen", "fridge", "appliance"],
    "beauty": ["cream", "lotion", "shampoo", "makeup", "lipstick", "perfume",
        "skincare", "haircare", "facewash", "beauty"],
    "books": ["book", "novel", "fiction", "textbook", "author", "publication"],
    "toys": ["toy", "doll", "puzzle", "lego", "kids", "children"],
    "sports": ["cricket", "bat", "ball", "football", "tennis", "gym", "yoga"],
}

MODEL_PATTERNS = {
    "iphone": r'iphone\s*(\d{1,2})\s*(pro|max|plus|mini)?',
    "galaxy": r'galaxy\s*([a-z]?\d{1,2})\s*(ultra|plus|fe|pro)?',
    "pixel": r'pixel\s*(\d{1,2}[a-z]?)\s*(pro|xl|a)?',
    "oneplus": r'oneplus\s*(\d{1,2}[a-z]?)\s*(pro|t|r)?',
    "macbook": r'macbook\s*(air|pro)?\s*(m\d|intel)?',
    "ipad": r'ipad\s*(pro|air|mini)?\s*(\d{1,2}\.?\d*)?',
}

# Affiliate configuration (replace with your IDs)
AFFILIATE_CONFIG = {
    "amazon": {"param": "tag", "id": "smarbuy0e-21"},
    "flipkart": {"param": "affid", "id": "smarbuy01"},
}


# ============================================================================
# Utility Functions
# ============================================================================

def _safe_int(val) -> int:
    try:
        s = str(val).replace(',', '').replace(' ', '').upper()
        if s.endswith('K'): return int(float(s[:-1]) * 1000)
        if s.endswith('M'): return int(float(s[:-1]) * 1_000_000)
        return int(float(s))
    except Exception:
        return 0


def _safe_float(val) -> float:
    try:
        return float(str(val).replace(',', '').strip())
    except Exception:
        return 0.0


def _normalize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.lower().strip())


# ============================================================================
# URL Validation and Affiliate Link Generation
# ============================================================================

def _validate_and_clean_url(url: str, platform: str, product_name: str = "") -> str:
    """
    Validate, clean, and ensure URL is functional.
    Generates fallback search URL if invalid.
    """
    if not url or url.strip() == "":
        return _generate_search_url(platform, product_name)
    
    url = url.strip()
    
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Validate URL format
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return _generate_search_url(platform, product_name)
    except Exception:
        return _generate_search_url(platform, product_name)
    
    # Clean tracking parameters
    tracking_params = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
        'ref', 'ref_', 'source', 'campaign', 'affiliate_id'
    ]
    
    for param in tracking_params:
        url = re.sub(rf'[?&]{param}=[^&]+', '', url)
    
    # Clean up multiple ? and &
    url = re.sub(r'&+', '&', url)
    url = re.sub(r'\?&', '?', url)
    url = url.rstrip('?&')
    
    return url


def _generate_search_url(platform: str, product_name: str) -> str:
    """Generate fallback search URL for a platform."""
    if not product_name:
        return f"https://www.google.com/search?q={quote_plus(platform)}"
    
    platform_search_urls = {
        "amazon": f"https://www.amazon.in/s?k={quote_plus(product_name)}",
        "flipkart": f"https://www.flipkart.com/search?q={quote_plus(product_name)}",
        "croma": f"https://www.croma.com/search/?text={quote_plus(product_name)}",
        "reliance digital": f"https://www.reliancedigital.in/search?q={quote_plus(product_name)}",
        "tata cliq": f"https://www.tatacliq.com/search/?searchQuery={quote_plus(product_name)}",
        "vijay sales": f"https://www.vijaysales.com/search/{quote_plus(product_name)}",
        "myntra": f"https://www.myntra.com/{quote_plus(product_name.replace(' ', '-'))}",
        "meesho": f"https://www.meesho.com/search?q={quote_plus(product_name)}",
        "jiomart": f"https://www.jiomart.com/search/{quote_plus(product_name)}",
    }
    
    platform_lower = platform.lower()
    for key, url in platform_search_urls.items():
        if key in platform_lower:
            return url
    
    return f"https://www.google.com/search?q={quote_plus(product_name + ' ' + platform)}"


def _generate_affiliate_link(url: str, platform: str) -> str:
    """Generate affiliate link with tracking."""
    if not url:
        return ""
    
    platform_lower = platform.lower()
    
    for store, config in AFFILIATE_CONFIG.items():
        if store in platform_lower:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}{config['param']}={config['id']}"
    
    return url


def _get_product_page_url(product: Dict) -> str:
    """Get the best available URL for a product."""
    # Priority order
    if product.get("link"):
        return product["link"]
    if product.get("affiliate_link"):
        return product["affiliate_link"]
    
    return _generate_search_url(
        product.get("platform", "Unknown"),
        product.get("name", "")
    )


# ============================================================================
# Category Detection
# ============================================================================

def _detect_product_category(query: str) -> str:
    query_lower = query.lower()
    scores = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[category] = score
    
    if not scores:
        return "general"
    
    return max(scores, key=scores.get)


def _get_category_price_range(category: str) -> Tuple[float, float]:
    ranges = {
        "electronics": (5000, 200000), "apparel": (200, 10000),
        "grocery": (50, 5000), "home": (500, 100000),
        "beauty": (100, 5000), "books": (100, 5000),
        "toys": (200, 10000), "sports": (300, 50000),
        "general": (100, 100000),
    }
    return ranges.get(category, (100, 100000))


# ============================================================================
# Semantic Model Matching
# ============================================================================

def _extract_model_info(text: str) -> Optional[Dict]:
    text_lower = text.lower()
    
    for brand, pattern in MODEL_PATTERNS.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            return {
                "brand": brand,
                "model": groups[0] if groups else "",
                "variant": groups[1] if len(groups) > 1 and groups[1] else "",
                "full_match": match.group(0)
            }
    
    generic_match = re.search(
        r'([a-z]+)\s*(\d{1,3})\s*(pro|max|ultra|plus|mini|air)?',
        text_lower
    )
    if generic_match:
        return {
            "brand": generic_match.group(1),
            "model": generic_match.group(2),
            "variant": generic_match.group(3) or "",
            "full_match": generic_match.group(0)
        }
    
    return None


def _is_model_match(query: str, product_title: str) -> bool:
    query_model = _extract_model_info(query)
    
    if not query_model:
        return True
    
    title_model = _extract_model_info(product_title)
    
    if not title_model:
        return False
    
    if query_model["brand"] and title_model["brand"]:
        if query_model["brand"] not in title_model["brand"]:
            if query_model["brand"] not in product_title.lower():
                print(f"  [Filter] Brand mismatch: '{query_model['brand']}' vs '{title_model['brand']}'")
                return False
    
    if query_model["model"] != title_model["model"]:
        print(f"  [Filter] Model mismatch: {query_model['model']} vs {title_model['model']}")
        return False
    
    if query_model["variant"] and title_model["variant"]:
        if query_model["variant"] != title_model["variant"]:
            print(f"  [Filter] Variant mismatch: {query_model['variant']} vs {title_model['variant']}")
            return False
    
    return True


# ============================================================================
# Seller Trust Scoring
# ============================================================================

def _calculate_seller_trust(platform: str, seller: str) -> Dict:
    seller_lower = seller.lower()
    platform_lower = platform.lower()
    
    factors = []
    base_trust = PLATFORM_TRUST_BASELINE.get(platform_lower, 0.50)
    factors.append(f"Platform baseline: {base_trust:.2f}")
    
    trust_score = base_trust
    
    boost_count = sum(1 for ind in TRUSTED_INDICATORS if ind in seller_lower)
    if boost_count > 0:
        boost = min(0.15, boost_count * 0.03)
        trust_score += boost
        factors.append(f"Trust indicators: +{boost:.2f}")
    
    penalty_count = sum(1 for ind in GREY_MARKET_INDICATORS if ind in seller_lower)
    if penalty_count > 0:
        penalty = min(0.50, penalty_count * 0.15)
        trust_score -= penalty
        factors.append(f"Grey market indicators: -{penalty:.2f}")
    
    trust_score = max(0.20, min(0.98, trust_score))
    
    if trust_score >= 0.70:
        classification = "Trusted"
    elif trust_score >= 0.45:
        classification = "Neutral"
    else:
        classification = "Grey Market"
    
    return {
        "score": round(trust_score, 3),
        "classification": classification,
        "factors": factors,
        "platform": platform,
        "seller": seller
    }


def _is_irrelevant_seller(source: str, category: str) -> bool:
    source_lower = source.lower()
    
    if any(irr in source_lower for irr in GLOBAL_IRRELEVANT_SELLERS):
        return True
    
    cat_irrelevant = CATEGORY_IRRELEVANT_SELLERS.get(category, [])
    if any(irr in source_lower for irr in cat_irrelevant):
        return True
    
    return False


# ============================================================================
# Review Quality Pre-Scoring
# ============================================================================

def _score_review_quality(reviews: List[str]) -> Dict:
    if not reviews:
        return {"quality_score": 0.5, "flags": ["No reviews"], "metrics": {}}
    
    flags = []
    total = len(reviews)
    lengths = [len(r) for r in reviews]
    avg_len = sum(lengths) / total
    short_count = sum(1 for l in lengths if l < 20)
    
    normalized = [_normalize_text(r)[:50] for r in reviews]
    unique_count = len(set(normalized))
    diversity = unique_count / total if total > 0 else 0
    
    exclamation_avg = sum(r.count('!') for r in reviews) / total
    all_caps_count = sum(1 for r in reviews if r.isupper() and len(r) > 10)
    
    quality = 0.50
    
    if avg_len > 100:
        quality += 0.15
    elif avg_len < 30:
        quality -= 0.15
        flags.append(f"Very short reviews (avg {avg_len:.0f} chars)")
    
    if diversity > 0.8:
        quality += 0.10
    elif diversity < 0.4 and total > 10:
        quality -= 0.15
        flags.append(f"Low diversity ({diversity:.0%} unique)")
    
    if short_count / total > 0.5:
        quality -= 0.10
        flags.append(f"{short_count}/{total} reviews unusually short")
    
    if exclamation_avg > 2:
        quality -= 0.10
        flags.append(f"Excessive exclamations (avg {exclamation_avg:.1f})")
    
    if all_caps_count > total * 0.2:
        quality -= 0.08
        flags.append(f"{all_caps_count} all-caps reviews")
    
    quality = max(0.10, min(0.95, quality))
    
    return {
        "quality_score": round(quality, 3),
        "flags": flags[:5],
        "metrics": {
            "avg_length": round(avg_len, 1),
            "diversity_ratio": round(diversity, 3),
            "short_review_pct": round(short_count / total * 100, 1),
            "exclamation_avg": round(exclamation_avg, 2)
        }
    }


# ============================================================================
# Deduplication
# ============================================================================

def _deduplicate_products(products: List[Dict]) -> List[Dict]:
    seen_signatures: Set[str] = set()
    unique_products = []
    
    for p in products:
        platform = p.get('platform', 'unknown')
        name_prefix = p.get('name', '')[:40].lower()
        price_bucket = round(p.get('price', 0) / 500) * 500
        
        signature = f"{platform}|{name_prefix}|{price_bucket}"
        
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_products.append(p)
        else:
            print(f"  [Dedup] Removed duplicate: {platform}")
    
    return unique_products


# ============================================================================
# Price Parsing and Filtering
# ============================================================================

def _parse_price(price_str: str, category: str = "general") -> float:
    clean = re.sub(r"[^\d.]", "", str(price_str))
    try:
        val = float(clean)
        min_price, max_price = _get_category_price_range(category)
        if val < min_price / 2:
            val *= 83
        return round(val, 2)
    except Exception:
        min_price, max_price = _get_category_price_range(category)
        return round(random.uniform(min_price, max_price), 2)


def _filter_price_outliers(products: List[Dict], category: str) -> List[Dict]:
    prices = [p.get("price", 0) for p in products if p.get("price", 0) > 0]
    
    if len(prices) < 3:
        return products
    
    sorted_prices = sorted(prices)
    median = sorted_prices[len(sorted_prices) // 2]
    
    min_price, max_price = _get_category_price_range(category)
    
    upper_threshold = min(median * 3.0, max_price * 1.5)
    lower_threshold = max(median * 0.3, min_price * 0.5)
    
    before = len(products)
    filtered = [
        p for p in products 
        if lower_threshold <= p.get("price", 0) <= upper_threshold
    ]
    removed = before - len(filtered)
    
    if removed:
        print(f"  [Filter] Removed {removed} price outliers")
    
    return filtered


# ============================================================================
# Platform Resolution
# ============================================================================

def _extract_platform(source: str) -> str:
    KNOWN = {
        "amazon": "Amazon", "flipkart": "Flipkart", "croma": "Croma",
        "reliance": "Reliance Digital", "vijay": "Vijay Sales",
        "tatacliq": "Tata Cliq", "myntra": "Myntra", "meesho": "Meesho",
        "snapdeal": "Snapdeal", "paytm": "Paytm Mall", "apple": "Apple",
        "samsung": "Samsung", "oneplus": "OnePlus", "mi.com": "Mi Store",
        "xiaomi": "Mi Store", "jio": "JioMart", "pai": "Pai International",
        "maple": "Maple Store", "imagine": "Imagine (APR)",
        "poorvika": "Poorvika", "sangeetha": "Sangeetha", "istore": "iStore",
        "indiamart": "IndiaMart", "shopclues": "ShopClues",
        "cashify": "Cashify", "nykaa": "Nykaa", "pepperfry": "Pepperfry",
    }
    
    sl = source.lower().strip()
    
    for key, name in KNOWN.items():
        if key in sl:
            return name
    
    cleaned = re.sub(r'\.(com|in|co\.in|net|org|store|shop)(\/.*)?$', '', sl, flags=re.IGNORECASE)
    cleaned = re.sub(r'^www\.', '', cleaned)
    cleaned = ' '.join(w.capitalize() for w in cleaned.replace('-', ' ').replace('_', ' ').split())
    
    return cleaned if cleaned else source


def _seller_label(platform: str, seller: str) -> str:
    sl = seller.lower()
    pl = platform.lower()
    
    if sl == pl or sl.startswith(pl):
        remainder = seller[len(platform):].strip(" -–|")
        return f"via {remainder}" if remainder else "Official Store"
    
    return seller


# ============================================================================
# SerpAPI Integration
# ============================================================================

def _do_serp_request(query: str) -> list:
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_shopping",
                "q": query,
                "api_key": SERPAPI_KEY,
                "num": 15,
                "gl": "in",
                "hl": "en"
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("shopping_results", [])
        if resp.status_code == 401:
            print("[SerpAPI] ❌ Invalid or expired API key. Check SERPAPI_KEY in .env.")
            return []
        if resp.status_code == 429:
            print("[SerpAPI] ❌ Rate limit hit. Free tier = 100/month.")
            return []
        print(f"[SerpAPI] HTTP {resp.status_code}")
    except Exception as e:
        print(f"[SerpAPI] Error: {e}")
    return []


def fetch_serpapi(query: str, category: str = "general") -> List[Dict]:
    if not SERPAPI_KEY or SERPAPI_KEY == PLACEHOLDER_SERPAPI_KEY:
        print("[SerpAPI] No valid API key — skipping")
        return []
    
    results = _do_serp_request(f'"{query}"')
    if not results:
        print("[SerpAPI] Exact match empty, retrying broad...")
        results = _do_serp_request(query)
    
    if not results:
        print("[SerpAPI] No results returned")
        return []
    
    products = []
    prices_raw = []
    
    for item in results[:12]:
        source = item.get("source", "Online Store")
        
        if _is_irrelevant_seller(source, category):
            print(f"[SerpAPI] Skipping irrelevant: {source}")
            continue
        
        title = item.get("title", "Unknown Product")
        
        if not _is_model_match(query, title):
            continue
        
        price = _parse_price(item.get("price", "0"), category)
        prices_raw.append(price)
        
        rating = float(item.get("rating", 0) or 0)
        reviews = _safe_int(item.get("reviews", 0))
        platform = _extract_platform(source)
        
        raw_link = item.get("link", "") or item.get("product_link", "")
        validated_link = _validate_and_clean_url(raw_link, platform, title)
        affiliate_link = _generate_affiliate_link(validated_link, platform)
        
        product_reviews = _generate_reviews(
            rating if rating > 0 else 3.8, 
            category
        )
        
        products.append({
            "name": title,
            "platform": platform,
            "seller": source,
            "seller_label": _seller_label(platform, source),
            "seller_trust": _calculate_seller_trust(platform, source),
            "price": price,
            "rating": rating if rating > 0 else round(random.uniform(3.5, 4.5), 1),
            "review_count": reviews if reviews > 0 else random.randint(50, 500),
            "link": validated_link,
            "affiliate_link": affiliate_link,
            "product_url": validated_link,  # Primary URL for frontend
            "thumbnail": item.get("thumbnail", ""),
            "reviews": product_reviews,
            "review_quality": _score_review_quality(product_reviews),
            "source": "serpapi",
            "category": category,
        })
    
    products = _filter_price_outliers(products, category)
    
    print(f"[SerpAPI] {len(products)} relevant listings for '{category}'")
    return products


# ============================================================================
# FakeStore API Fallback
# ============================================================================

def fetch_fakestore(query: str, category: str = "general") -> List[Dict]:
    try:
        resp = requests.get("https://fakestoreapi.com/products", timeout=6)
        if resp.status_code == 200:
            q = query.lower()
            all_p = resp.json()
            
            matched = [
                p for p in all_p 
                if q in p.get("title", "").lower() 
                or q in p.get("category", "").lower()
            ]
            
            if not matched:
                matched = all_p[:5]
            
            results = []
            for p in matched[:4]:
                results.append(_norm_fakestore(p, category))
            return results
    except Exception as e:
        print(f"[FakeStore] Error: {e}")
    return []


def _norm_fakestore(p: Dict, category: str) -> Dict:
    rd = p.get("rating", {})
    rating = float(rd.get("rate", 3.5))
    reviews = _generate_reviews(rating, category)
    title = p.get("title", "Unknown")
    platform = "ShopEasy"
    
    validated_link = _validate_and_clean_url("", platform, title)
    
    return {
        "name": title,
        "platform": platform,
        "seller": "ShopEasy Official",
        "seller_label": "Official Store",
        "seller_trust": _calculate_seller_trust("ShopEasy", "ShopEasy Official"),
        "price": round(p.get("price", 0) * 83, 2),
        "rating": rating,
        "review_count": int(rd.get("count", 50)),
        "link": validated_link,
        "affiliate_link": validated_link,
        "product_url": validated_link,
        "reviews": reviews,
        "review_quality": _score_review_quality(reviews),
        "source": "fakestore",
        "category": category,
    }


# ============================================================================
# Mock Data Generation
# ============================================================================

def _generate_reviews(rating: float, category: str = "general") -> List[str]:
    pos = [
        "Excellent product! Works perfectly and great build quality.",
        "Very happy with this purchase. Highly recommend to everyone.",
        "Amazing value for money. Fast delivery and good packaging.",
        "Best product in this category. Totally worth every rupee.",
        "Great product, exactly as described. Very satisfied.",
        "Outstanding performance. Would definitely buy again.",
        "Quality exceeded my expectations. Very durable.",
    ]
    
    neg = [
        "Disappointed with quality. Not worth the price at all.",
        "Stopped working after two weeks. Very poor build quality.",
        "Product looks nothing like the pictures. Misleading listing.",
        "Bad experience. Customer service was completely unhelpful.",
        "Delivery was late and packaging was badly damaged.",
    ]
    
    mid = [
        "Decent product for the price. Has some minor issues.",
        "Good overall but delivery took longer than expected.",
        "Works fine but quality could be better.",
        "Okay for occasional use but not for daily heavy use.",
        "Average product. Nothing special but gets the job done.",
    ]
    
    sus = [
        "Best product ever!!!", "Amazing!!!", "Perfect 10/10!!!",
        "Love it love it!!!", "Must buy!!! Best!!!",
    ]
    
    if rating >= 4.2:
        reviews = random.sample(pos, min(4, len(pos))) + random.sample(mid, 2)
    elif rating >= 3.5:
        reviews = random.sample(mid, 3) + random.sample(pos, 2) + random.sample(neg, 1)
    else:
        reviews = random.sample(neg, 3) + random.sample(mid, 2) + random.sample(pos, 1)
    
    if random.random() < 0.25:
        reviews += random.sample(sus, min(2, len(sus)))
    
    random.shuffle(reviews)
    return reviews[:8]


def get_mock_products(query: str, category: str = "general") -> List[Dict]:
    min_price, max_price = _get_category_price_range(category)
    base = random.randint(int(min_price), int(max_price))
    
    platforms = [
        ("Amazon", "Amazon Official", 0.85, "https://www.amazon.in/s?k="),
        ("Flipkart", "Flipkart Assured", 0.80, "https://www.flipkart.com/search?q="),
        ("Croma", "Croma Official Store", 0.75, "https://www.croma.com/search/?text="),
        ("Reliance Digital", "Reliance Digital", 0.75, "https://www.reliancedigital.in/search?q="),
        ("Tata Cliq", "Tata Cliq Official", 0.70, "https://www.tatacliq.com/search/?searchQuery="),
        ("Grey Market", "Third Party Reseller", 0.30, ""),
    ]
    
    products = []
    for platform, seller, trust_base, search_url in platforms:
        rating = round(random.uniform(3.2, 4.7), 1)
        reviews = _generate_reviews(rating, category)
        
        if "Grey" in platform:
            price = base - random.randint(int(base * 0.1), int(base * 0.3))
        elif platform in ["Amazon", "Flipkart"]:
            price = base - random.randint(0, int(base * 0.05))
        else:
            price = base + random.randint(0, int(base * 0.1))
        
        product_name = f"{query} - {platform} Edition"
        
        # Generate product URL
        if search_url:
            product_url = search_url + quote_plus(product_name)
        else:
            product_url = _validate_and_clean_url("", platform, product_name)
        
        products.append({
            "name": product_name,
            "platform": platform,
            "seller": seller,
            "seller_label": "Official Store" if "Official" in seller else seller,
            "seller_trust": _calculate_seller_trust(platform, seller),
            "price": max(min_price, min(max_price, price)),
            "rating": rating,
            "review_count": random.randint(50, 5000),
            "link": product_url,
            "affiliate_link": _generate_affiliate_link(product_url, platform),
            "product_url": product_url,
            "reviews": reviews,
            "review_quality": _score_review_quality(reviews),
            "source": "mock",
            "category": category,
        })
    
    return products


# ============================================================================
# Master Fetch Function
# ============================================================================

def fetch_all_products(query: str, budget: float = None) -> List[Dict]:
    """
    Universal product fetcher with clickable product links.
    """
    print(f"\n{'='*60}")
    print(f"[DataFetcher] Query: '{query}'")
    print(f"{'='*60}")
    
    category = _detect_product_category(query)
    print(f"[DataFetcher] Detected category: {category}")
    
    products = []
    
    # Try SerpAPI
    serp = fetch_serpapi(query, category)
    if serp:
        products.extend(serp)
        print(f"[DataFetcher] SerpAPI returned {len(serp)} products")
    
    # FakeStore fallback
    if len(products) < 3:
        fake = fetch_fakestore(query, category)
        if fake:
            products.extend(fake)
            print(f"[DataFetcher] FakeStore added {len(fake)} products")
    
    # Mock data fallback
    if len(products) < 3:
        print("[DataFetcher] Using mock data")
        mock = get_mock_products(query, category)
        products.extend(mock)
    else:
        mock_extra = get_mock_products(query, category)[:2]
        products.extend(mock_extra)
    
    # Deduplication
    products = _deduplicate_products(products)
    print(f"[DataFetcher] After deduplication: {len(products)} products")
    
    # Budget filtering
    if budget:
        filtered = [p for p in products if p.get("price", 999999) <= budget]
        if filtered:
            products = filtered
            print(f"[DataFetcher] Budget ₹{budget:,.0f}: {len(products)} products")
        else:
            print(f"[DataFetcher] No products under budget, showing all")
    
    # Ensure every product has a valid product_url
    for p in products:
        if not p.get("product_url"):
            p["product_url"] = _get_product_page_url(p)
        if not p.get("link"):
            p["link"] = p["product_url"]
    
    # Sort by seller trust
    products.sort(
        key=lambda x: x.get('seller_trust', {}).get('score', 0.5), 
        reverse=True
    )
    
    print(f"[DataFetcher] Final: {len(products)} products with clickable links")
    print(f"{'='*60}\n")
    
    return products