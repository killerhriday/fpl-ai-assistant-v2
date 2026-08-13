# 🚀 FPL AI Assistant v2 — Ultimate Developer & AI Context Guide

> **Last Updated:** August 14, 2026
> **Author:** Built & enhanced with AI-assisted development
> **Purpose:** This file exists specifically to provide extremely strong, detailed context to any AI or human developer who pulls this code and attempts to modify it. **READ EVERY WORD OF THIS BEFORE MODIFYING THE CODEBASE.**

---

## ⚠️ FOR AI DEVELOPERS (CRITICAL CONTEXT)
**If you are an AI reading this repo to make updates, read this section carefully to avoid breaking the application. The logic in this app is highly fragile due to the nature of OCR and FPL API quirks.**

### 1. 🧠 Spatial OCR Engine (DO NOT REVERT TO FLAT OCR)
- The original OCR approach (flat text scanning) failed miserably due to noise from the screenshot (like UI buttons and shirt sponsors).
- We have implemented a **Strict Spatial OCR Engine** (`backend/services/ocr.py`) using `easyocr` and OpenCV.
- **How it works:** It groups text bounding boxes into **Y-coordinate rows** (top to bottom).
- **Row Mapping is strict:**
  - Row 0 (Top) = Goalkeeper (GK)
  - Row 1 = Defenders (DEF)
  - Row 2 = Midfielders (MID)
  - Row 3 = Forwards (FWD)
  - Row 4 = Bench (4 players)
- **CRITICAL RULE:** **Do not** attempt to determine player positions by looking them up in the FPL database! The app **must** rely on their physical placement (Y-coordinate rows) on the screen to construct the original user squad accurately. The user's screenshot layout dictates the formation.

### 2. 🛡️ Noise Filtering & Blocklists (OCR)
- The app actively strips out "shirt sponsors" (Betano, Emirates, Etihad, AIA, etc.) and "team codes" (ARS, MUN, BOU) because they cause false-positive fuzzy matches with short player names (e.g. Betano -> Beto, BOU -> Botman).
- The fuzzy match threshold in `rapidFuzz` is set to **86**. Do not lower it, or junk text will leak into the squad.
- Minimum character length for matches is **4** (do not lower to 3).
- Hard cap of **15 players** is strictly enforced.

### 3. ⚽ FPL Formation Rules & Recommendation Engine
- An FPL squad must ALWAYS have exactly 15 players: **2 GKs, 5 DEFs, 5 MIDs, 3 FWDs**.
- The starting 11 formation **must** adhere to these strict limits:
  - Exactly **1 GK**
  - Minimum **3 DEF** (up to 5)
  - Minimum **2 MID** (up to 5)
  - Minimum **1 FWD** (up to 3)
- **Transfers:** Transfers in FPL are strictly **position-for-position** (e.g., you can only trade a DEF for a DEF).
- **Formation Changes:** While transfers are position-for-position, the AI recommendation engine (`backend/services/analytics.py`) calculates the **Absolute Optimal 11 starters** for any hypothetical 15-man squad. If a position-for-position transfer results in a different optimal 11 (e.g., dropping a MID to the bench and starting a new DEF), the AI will recommend a **formation change** (e.g., from 3-4-3 to 4-3-3).

### 4. 🌐 Data Freshness & Caching
- The backend fetches from the official FPL bootstrap API (`https://fantasy.premierleague.com/api/bootstrap-static/`).
- `teams_map` is crucial. The frontend expects club short names (like "ARS"), not IDs (like "1"). This mapping happens in `main.py` before `format_player` is called.
- `code` field is used for player photos (`p{code}.png`), **not** the `photo` field (which is broken and returns 404s in the FPL API).

### 5. ⚡ Dynamic Data Generation (No LLM Calls)
- The "Latest News", "Transfer Recommendations", and "AI Summary" sections are all generated **deterministically** via Python logic in `backend/services/analytics.py`. 
- **Do not** try to plug an external LLM (like OpenAI) into these routes. The app is designed to run locally, reliably, and fast.

---

## 📖 What is this App?
**FPL AI Assistant v2** is a computer-vision powered web application designed to help Fantasy Premier League (FPL) managers optimize their squads. 

Instead of requiring users to manually log in with their FPL credentials (which violates terms of service and risks bans), this app uses **Optical Character Recognition (OCR)**. Users simply upload a screenshot of their FPL pitch, and the app instantly "reads" the image to identify their squad, checks live API data for injuries/prices, and uses a deterministic algorithm to recommend the statistically optimal transfer.

## 🎮 How to Use It (Step-by-Step)
1. **Take a Screenshot:** Open your FPL team on your phone or computer and take a screenshot of the "Pitch View" (showing your 11 starters and 4 bench players).
2. **Upload:** Drag and drop the screenshot into the upload box on the left side of the app.
3. **Wait for Analysis:** The app will process the image (extracting names row-by-row), fetch the latest FPL data, and reconstruct your squad.
4. **Review Your Squad:** Check the "Original Team" pitch on the left to ensure the app correctly identified your formation and all 15 players. 
5. **View Recommendations:** The right column will show you:
   - **AI Suggested Team:** A visual representation of your squad *after* the recommended transfer.
   - **Recommended Transfers:** Exactly who to sell, who to buy, and the projected point gain.
   - **AI Summary:** A plain-English explanation of why the transfer was suggested.
6. **Check the Dashboards:** Use the "FPL Player Status Board" to check for league-wide injuries, the "Gameweek Fixtures" board for live scores and upcoming match times, and the "Latest FPL News" feed for dynamic data trends (like who is rising in price or being panic-sold).

---

## 🏗️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | React (Vite) |
| Backend | Python (FastAPI + Uvicorn) |
| OCR | EasyOCR + OpenCV preprocessing |
| Fuzzy Matching | RapidFuzz |
| Data Source | Official FPL API (`fantasy.premierleague.com`) |
| Image Processing | CLAHE, Gaussian Blur, 2x Upscaling |

---

## 🚀 How to Run

### Backend
```bash
cd backend
source venv/bin/activate
python main.py
```
Runs on `http://localhost:3001`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`
