"""
config.py
Central configuration — loads .env and exposes settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip().strip('"').strip("'")
PLACEHOLDER_SERPAPI_KEY = "eaa31779b6e6c9291a31c61fd912010f9905645e27079321b5a268792a138293"
DB_PATH     = os.getenv("DB_PATH", "smartbuy.db")
API_HOST    = os.getenv("API_HOST", "0.0.0.0")
API_PORT    = int(os.getenv("API_PORT", "8000"))

def serpapi_available() -> bool:
    return bool(SERPAPI_KEY and SERPAPI_KEY != PLACEHOLDER_SERPAPI_KEY)
