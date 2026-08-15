# 🚀 FPL AI Assistant v2 — Ultimate Developer API & ML Architecture

> **Last Updated:** August 15, 2026

Welcome to the **FPL AI Assistant v2**, a computer-vision powered web application and developer platform designed to help Fantasy Premier League (FPL) managers optimize their squads using advanced Scikit-Learn Predictive Machine Learning models and unrestricted deep data APIs.

## 🧠 Scikit-Learn ML Predictive Engine
Instead of relying on the basic, official FPL API `ep_next` predictions, this platform features a proprietary **Machine Learning Data Analytics Engine** (`backend/services/ml_engine.py`).
- **How it Works:** It uses a `RandomForestRegressor` trained natively in-memory on deep FPL metrics (ICT Index, Threat, Creativity, Form, points per game, and FDR).
- **The Result:** It generates a custom "True Score" for every player and dynamically injects this projection into the transfer algorithm.
- **Why it matters:** Standard FPL managers rely on basic form and price. The AI Assistant identifies massive differential opportunities (e.g. players with low points but immense underlying xG/xA) to build the Absolute Optimal 11 starters.

## 🌐 15+ Unrestricted FPL APIs (No Rate Limits)
The backend operates as a highly concurrent data hub. It exposes 15+ dedicated, unblocked API endpoints for developers wanting access to deep, normalized FPL data, raw ML projections, and price volatility.

### API Reference (Running on `http://localhost:3001`)

**Core Processing**
- `POST /api/process-team` - Upload a pitch screenshot for spatial OCR extraction and ML transfer optimization.
- `GET /api/process-team/{id}` - Poll for analysis completion.
- `GET /api/metadata` - Global gameweek data and Fixture Difficulty Rating (FDR) board.

**Players & Teams**
- `GET /api/v2/players` - Get all PL players.
- `GET /api/v2/players/{id}` - Deep stats for a specific player.
- `GET /api/v2/teams` - Get all PL teams.
- `GET /api/v2/teams/{id}` - Specific team roster and data.

**Fixtures & Gameweeks**
- `GET /api/v2/fixtures` - Every fixture in the season.
- `GET /api/v2/fixtures/live` - Live scores for the current active gameweek.

**Market Dynamics**
- `GET /api/v2/market/price-changes` - Daily risers and fallers.
- `GET /api/v2/market/transfers-in` - Top 20 players transferred in.
- `GET /api/v2/market/transfers-out` - Top 20 players transferred out (panic selling).
- `GET /api/v2/injuries` - Global injury, loan, and suspension list.
- `GET /api/v2/dream-team` - The current gameweek's highest scoring 11.

**Deep Analytics & ML**
- `GET /api/v2/stats/xg-xa` - Underlying Expected Goals (xG) and Expected Assists (xA) equivalents.
- `GET /api/v2/ml/projections` - Raw `RandomForestRegressor` ML point projections for the top 100 players.
- `GET /api/v2/system/health` - Check cache freshness and ML engine training status.

## 🏗️ Tech Stack
| Component | Technology |
|-----------|-----------|
| Frontend | React (Vite) |
| Backend | Python (FastAPI + Uvicorn) |
| ML Engine | Scikit-Learn, Pandas, NumPy |
| OCR | EasyOCR + OpenCV (Spatial Row Validation) |
| Fuzzy Matching | RapidFuzz |

## 🚀 How to Run

### Backend
```bash
cd backend
python -m pip install -r requirements.txt # (or manually install fastapi uvicorn scikit-learn pandas easyocr opencv-python rapidfuzz)
uvicorn main:app --port 3001 --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
