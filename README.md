# SmartBuy AI

SmartBuy AI is an intelligent product recommendation system that helps users discover the best-value products across online marketplaces. It combines product search, review analysis, suspicious-review detection, pricing logic, and seller trust scoring to recommend the most worthwhile purchase.

The project is designed as a Python-based AI pipeline with a FastAPI backend and a lightweight frontend demo.

## Why this project?

Shopping online often means comparing dozens of listings across platforms such as Amazon and Flipkart. SmartBuy AI simplifies that by:

- parsing user intent and budget constraints
- searching for matching products across sources
- normalizing and evaluating listings
- analyzing review sentiment and spotting fake or low-quality reviews
- scoring each product based on value, trust, and review quality
- recommending the best option with reasoning and alternatives

## Key Features

- AI-driven query planning
- Multi-source product fetcher with fallback data sources
- Review sentiment analysis using TextBlob with offline fallback logic
- Suspicious review detection heuristics
- Value scoring based on price, ratings, sentiment, review volume, and seller trust
- FastAPI backend with health and search endpoints
- CLI access for local usage
- Static frontend demo for quick interaction

## Architecture Overview

```text
User Query
   |
   v
Planner Agent
   |
   v
Search Agent --> Fetcher --> Product Listings
   |
   v
Analysis Agent --> Sentiment + Fake Review Check
   |
   v
Scoring Engine --> Weighted Value Score
   |
   v
Critic Agent --> Audit + penalty logic
   |
   v
Decision Agent --> Final recommendation
   |
   v
FastAPI / CLI / Frontend
```

## Project Structure

```text
SmartBuy/
├── agents/
│   ├── analysis_agent.py
│   ├── critic_agent.py
│   ├── decision_agent.py
│   ├── pipeline.py
│   ├── planner.py
│   └── search_agent.py
├── api/
│   └── main.py
├── data/
│   ├── fetcher.py
│   ├── mock_fetcher.py
│   └── serpapi_fetcher.py
├── database/
│   └── models.py
├── frontend/
│   └── index.html
├── nlp/
│   ├── fake_review_detector.py
│   └── sentiment.py
├── scoring/
│   └── value_score.py
├── .env.example        (if present in your environment setup)
├── .gitignore
├── config.py
├── requirements.txt
├── run_cli.py
├── start_server.py
├── smartbuy.db         (generated locally)
├── README.md
└── SmartBuyAI_IEEE_Final.pdf
```

## Getting Started

### Prerequisites

- Python 3.9+
- pip
- Internet access for live product retrieval (optional if using mock/fallback data)

### 1) Clone the repository

```bash
git clone https://github.com/Gaurav-negi1/Smart_buy.git
cd Smart_buy
```

### 2) Create and activate a virtual environment

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Create a `.env` file in the project root if you want to use live product search APIs.

```env
SERPAPI_KEY=your_serpapi_key_here
API_HOST=0.0.0.0
API_PORT=8000
```

If no valid SerpAPI key is provided, the app can still fall back to mock/demo data for local testing.

## Running the App

### Option A: Command-line usage

```bash
python run_cli.py "Samsung Galaxy under 60000"
```

This runs the SmartBuy pipeline directly from the terminal and prints the best recommendation.

### Option B: Start the API server

```bash
python start_server.py
```

Then open:

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Option C: Open the frontend demo

Open `frontend/index.html` in a browser.

Note: the static HTML demo is meant for quick demonstration; the backend server is the primary operational interface.

## API Endpoints

### Health check

```bash
curl http://localhost:8000/health
```

Response:

```json
{"status": "ok"}
```

### Product search

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "iPhone 15 under 70000",
    "budget": 70000
  }'
```

### Search history

```bash
curl "http://localhost:8000/history?limit=10"
```

## Example Recommendation Output

```json
{
  "query": "Samsung Galaxy under 60000",
  "recommended_platform": "Amazon",
  "product_name": "Samsung Galaxy M34 5G",
  "price": 21999,
  "rating": 4.4,
  "value_score": 86.2,
  "risk_level": "Low",
  "reason": "Top value score of 86.2/100. strong rating 4.4/5. within ₹60,000 budget.",
  "alternatives": [
    {"platform": "Flipkart", "name": "Samsung Galaxy M33", "price": 22999, "value_score": 82.1}
  ]
}
```

## How the Recommendation Logic Works

The pipeline follows this process:

1. Planner extracts the product, budget, and preference hints.
2. Search agent fetches candidate products from available sources.
3. Analysis agent processes review text for sentiment and suspicious patterns.
4. Scoring engine computes weighted value based on:
   - rating
   - sentiment score
   - review volume
   - price advantage
   - seller trust
5. Critic agent audits the score and penalizes anomalies.
6. Decision agent selects the best recommendation and returns alternatives.

## Commands Summary

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI search
python run_cli.py "Samsung Galaxy under 60000"

# Start backend
python start_server.py

# Test API health
curl http://localhost:8000/health
```

## Notes

- The system is optimized for local experimentation and demos.
- Live marketplace retrieval depends on data source availability and API credentials.
- The fake review detector and sentiment analysis are heuristic and designed for offline, low-cost analysis.
- Search result quality improves when the query is specific and includes product names, variants, or a clear budget.

## Future Improvements

- Add more marketplaces and data providers
- Improve review and seller classification accuracy
- Add authentication and user history persistence
- Add a richer front-end dashboard
- Add unit tests and CI pipeline

## License

No explicit license file is included in the repository at the moment. If this project is intended for public release, add an appropriate license such as MIT or Apache 2.0 before distribution.

## Contributing

Contributions are welcome. If you want to improve the recommendation logic, add new marketplaces, or refine the scoring model, open a pull request with a clear summary of the changes.
