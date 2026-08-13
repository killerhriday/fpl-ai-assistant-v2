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

## 🆕 Latest Updates (August 2026)

Here is a complete list of everything we just built and updated in the application right now:

1. **Animated Football Upload UI**: Completely replaced the generic globe icon in the drag-and-drop zone with a custom, playfully animated football (soccer ball) SVG that kicks and bounces, giving the app a premium sports feel.
2. **Multi-Transfer Engine Upgrade**: Upgraded the transfer algorithm to handle 1 to 5 simultaneous transfers based on available Free Transfers. It strictly enforces at least 1 transfer if free transfers are available (preventing idle hoarding).
3. **Dynamic Point-Hit Calculator**: The transfer engine now mathematically penalizes recommendations that exceed the user's free transfer limit, automatically deducting a 4-point hit per extra transfer from the projected gain.
4. **Strict Spatial OCR Validation**: Hardened the Computer Vision OCR pipeline by ripping out the old, fuzzy-matching approach and replacing it with strict Y-coordinate bounding boxes to eliminate false positives from shirt sponsors and UI artifacts.
5. **Captaincy UI Simplification**: Removed the error-prone Captain (C) and Vice-Captain (V) detection logic (which failed on compressed screenshots) and completely stripped the captaincy badges and point-doubling from the UI, opting for a much cleaner pitch layout focused entirely on base projected points.
6. **Backend Server Fixes**: Removed hallucinated placeholder functions (`_detect_powerups`) and fixed variable reassignment bugs in the Spatial Player Matching pipeline to ensure rock-solid stability.

## ✨ What We Built (The Super Long Feature List)

Here is a comprehensive list of everything implemented in this application to ensure maximum performance and FPL optimization:

1.  **Deep Thinking Multi-Transfer Optimization Algorithm**: A greedy computational engine that breaks past single-transfer limits. It analyzes up to 5 simultaneous transfers (based on the user's available Free Transfers), looking at long-term projected points, to execute multi-step squad overhauls only when mathematically justified.
2.  **Strict Spatial OCR Engine with Computer Vision**: We rebuilt the OCR pipeline using OpenCV and EasyOCR to scan the screenshot structurally. It enforces Y-coordinate bounding boxes (Top=GK, Row2=DEF, Row3=MID, Row4=FWD, Bottom=Bench) rather than blindly fuzzy matching, completely eradicating false positives from shirt sponsors and UI artifacts.
3.  **Captain (C) & Vice-Captain (V) Graceful Assignment**: FPL badges are microscopic and often corrupted by image artifacts. The engine gracefully bypasses OCR limitations by calculating the highest `ep_next` (projected points) earners in the original squad and natively rendering the (C) and (V) UI badges, perfectly reflecting optimal real-world user behavior.
4.  **Double Points Calculation Engine**: The AI automatically doubles the projected points for the active Captain (and falls back to Vice-Captain dynamically if needed), accurately representing total score projections.
5.  **Multi-Transfer Points Hit Calculator**: If the user has fewer free transfers than the optimal strategy suggests, the algorithm automatically deducts a standard 4-point penalty per additional transfer and strictly enforces at least 1 transfer if free transfers are available (so it never idly hoards).
5.  **Real-Time Fixture Difficulty Rating (FDR) Table**: A live data board located beneath the gameweek fixtures that pulls the exact next 5 matches for all 20 Premier League teams. It applies the official FPL color scale (Difficulty 1-5, Dark Green to Dark Red) natively.
6.  **Sleek, Premium Dark-Mode UI Re-design**: Complete CSS overhaul featuring HSL-tailored colors, dynamic hover states, responsive layouts, micro-animations on load, and a beautifully rendered interactive football pitch.
7.  **Dynamic Formation Shift Engine**: The AI evaluates the Absolute Optimal 11 starters. If a recommended transfer triggers a more mathematically sound formation (e.g., dropping a 5th defender for a 3rd striker), the UI visually updates the pitch and badges the new formation (e.g., "3-4-3 to 4-3-3").
8.  **Global Player Status & Injury Dashboard**: Pulls the `status` and `news` arrays from the FPL API and generates a color-coded "Pill" dashboard showing exactly who is injured, suspended, doubtful (with % chance), or loaned out across the entire league.
9.  **Live Gameweek Fixtures Feed**: Monitors the `is_current` FPL event, rendering live scores, match status (LIVE, Upcoming, FT), and team logos dynamically on the main dashboard.
10. **Deterministic "Fake AI" News Generation**: Instead of relying on expensive, slow, and hallucination-prone LLMs, the app computes real-time data trends (highly transferred players, injuries) and deterministically generates "AI" news headlines and conversational squad summaries.
11. **Strict Budget & Bank Enforcement**: The app accurately calculates current squad value, identifies unspent money "In The Bank," and restricts the transfer engine to only suggest players within the exact affordable price limits.
12. **Playful Custom UI Elements**: Featuring a beautifully animated kicking and rolling football SVG in the drag-and-drop zone to ensure an engaging user experience, abandoning generic icons for custom FPL-flavored components.

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
