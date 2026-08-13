# 🚀 FPL AI Assistant v2 — Update Log

> **Last Updated:** August 14, 2026  
> **Author:** Built & enhanced with AI-assisted development

---

## ⚠️ FOR AI DEVELOPERS (CRITICAL CONTEXT)
**If you are an AI reading this repo to make updates, read this section carefully to avoid breaking the application.**

1. **Spatial OCR (DO NOT REVERT TO FLAT OCR):**
   - The original OCR approach (flat scanning) failed miserably due to noise. We have implemented a **Strict Spatial OCR Engine** (`backend/services/ocr.py`) using `easyocr` and OpenCV.
   - It works by grouping text bounding boxes into **Y-coordinate rows**.
   - **Row Mapping is strict:** Row 0 = GK, Row 1 = DEF, Row 2 = MID, Row 3 = FWD, Row 4 = Bench.
   - **Do not** attempt to determine player positions by looking them up in the FPL database. The app **must** rely on their physical placement on the screen to construct the original user squad accurately.

2. **Noise Filtering & Blocklists:**
   - The app actively strips out "shirt sponsors" (Betano, Emirates, Etihad, etc.) and "team codes" (ARS, MUN, BOU) because they cause false-positive fuzzy matches with short player names (e.g. Betano -> Beto, BOU -> Botman).
   - The fuzzy match threshold in `rapidFuzz` is set to **86**. Do not lower it, or junk text will leak into the squad.
   - Minimum character length for matches is **4** (do not lower to 3).
   - Hard cap of **15 players** is strictly enforced.

3. **Data Freshness & Caching:**
   - The backend fetches from the official FPL bootstrap API (`fantasy.premierleague.com/api/bootstrap-static/`).
   - `teams_map` is crucial. The frontend expects club short names (like "ARS"), not IDs (like "1"). This mapping happens in `main.py` before `format_player` is called.
   - `code` field is used for player photos (`p{code}.png`), **not** the `photo` field (which is broken in the FPL API).

4. **Dynamic Data Generation (No LLM Calls):**
   - The "Latest News", "Transfer Recommendations", and "AI Summary" sections are all generated **deterministically** via Python logic in `backend/services/analytics.py`. Do not try to plug an external LLM (like OpenAI) into these routes. It is designed to run locally and fast.

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

## ✅ Successfully Implemented Features

### 🧠 Spatial OCR Engine (Complete Rewrite)
The original OCR engine has been **completely rewritten from scratch** to be spatially aware.

**What it does now:**
- Reads the FPL pitch screenshot **row by row** (top → bottom)
- **Detects formation automatically** from the image layout (e.g. 3-4-3, 4-3-3, 4-4-2)
- Assigns player positions based on **WHERE they appear on the pitch**, not from the FPL database
- Row 0 (top of pitch) → GK
- Row 1 → DEF
- Row 2 → MID
- Row 3 → FWD
- Row 4+ → Bench (4 players)

**Noise filtering:**
- Filters out **shirt sponsor logos** (Betano, Emirates, Etihad, AIA, etc.) that were being matched to random players
- Filters out **3-letter team codes** (COV, BOU, FUL, BRE, etc.)
- Filters out **UI text** (Available, Gameweek, Deadline, Pitch, List, etc.)
- Filters out **fixture tags** like "BHA (A)" and "MCI (H)"
- Fuzzy match threshold set to **86** to prevent false positives
- Hard cap of **15 players max** to prevent noise overflow

---

### ⚽ Formation Detection
- Automatically counts players per row to detect formation
- Displays formation badge (e.g. `3-4-3`) on the pitch view
- Shown in the "My Team" panel as `Formation: 3-4-3 (11 starters, 4 bench)`

---

### 🖼️ Player Photos
- Uses the correct FPL API `code` field for player headshot URLs
- Photos now load reliably from `resources.premierleague.com`
- Fallback SVG silhouette for any missing photos

---

### 🏟️ Real Team Names
- Club names now show proper short names like **ARS**, **MUN**, **AVL**, **CHE**
- Previously showed raw team IDs like "Club 1", "Club 16"
- Teams map built from the official FPL bootstrap API

---

### 🩺 FPL Player Status Board
- Shows **ALL** flagged players across the entire Premier League (not limited to 15)
- Player categories with color coding:
  - 🔴 **Injured** — red text + red dot
  - 🟡 **Doubtful** — yellow text + yellow dot (includes chance %)
  - 🔴 **Suspended / Red Card** — dark red
  - ⚪ **Loaned / Unavailable** — gray
- Each entry shows:
  - Player **profile photo** with status badge overlay
  - Player name colored by severity
  - Team short name
  - Return date (when available)
  - News tooltip on hover
- **Scrollable container** — doesn't extend the page no matter how many entries

---

### 📊 Gameweek Fixtures Board
- Shows **all fixtures** for the current/upcoming gameweek in a clean 1-column layout
- Displays **full team names** (e.g., "Arsenal") and official **team logos** fetched directly from the Premier League CDN
- **Live scores** — green pulsing dot + score display for ongoing matches
- **Upcoming matches** — blue badge with formatted kickoff date & time
- **Finished matches** — dimmed with "Full Time" badge and final score
- Sorted: LIVE first → Upcoming → Finished

---

### 💰 Budget Calculator
- Calculates budget as: `£100m - total squad cost`
- Shows three metrics:
  - Squad Value
  - In The Bank
  - Total Budget
- Updates dynamically based on detected squad

---

### 🔄 Transfer Recommendations
- Deterministic analysis engine (no AI hallucination)
- Finds weakest starter and suggests best replacement
- Shows:
  - Player OUT → Player IN
  - Net projected point gain
  - Hit cost (if using extra transfers)
  - Price difference
  - Reasoning

---

### 🎨 UI/UX Polish
- **Pitch Design:** Realistic deep green grass texture with alternating stripes and translucent white chalk lines
- Smooth hover transitions on all interactive elements
- Custom scrollbar styling
- Centered pitch layout below the drag-and-drop upload
- Dark theme with clean visual hierarchy
- Formation badge on pitch view
- Responsive layout across all screen sizes

---

### 📰 Dynamic FPL News
- Generated completely on the fly from the FPL API (no external LLM calls or hardcoded mocks)
- Generates up to 8 real news stories based on data trends:
  - Most Transferred In / Out
  - Form Players
  - Price Risers / Fallers
  - Differential Picks (<5% ownership)
  - Ownership Stats & Expected Points Leaders
- Entire news cards are **clickable links** that open the official FPL statistics page

---

### 🤖 AI Summary
- Deterministic text engine that generates human-readable transfer advice
- Considers injuries, budget impact, and projected gains
- No external AI calls — runs entirely locally

---

### 🔒 Privacy
- Screenshots are processed in-memory and deleted after analysis
- No data is persisted to disk
- Privacy status shown in the timeline

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

---

## 📁 Key Files Modified

| File | What Changed |
|------|-------------|
| `backend/services/ocr.py` | Complete rewrite — spatial row-based OCR engine |
| `backend/services/analytics.py` | Player photos, team names, injury board, budget calc |
| `backend/main.py` | Spatial OCR integration, gameweek fixtures, teams map |
| `backend/models.py` | Added formation, gameweek_fixtures, photo_url fields |
| `frontend/src/App.jsx` | Formation display, fixtures board, photo status board |
| `frontend/src/index.css` | Fixtures CSS, formation badge, photo avatars, text colors |

---

## 📌 Known Limitations
- OCR requires minimum 4-character player names (very short names like "Son" may not match)
- Fixture live scores update when the page is refreshed (not real-time WebSocket)
- FPL data is cached for 1 hour — may be slightly delayed during active gameweeks
