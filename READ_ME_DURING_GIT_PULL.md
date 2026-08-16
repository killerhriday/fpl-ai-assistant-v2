# 🚨 CRITICAL INSTRUCTIONS FOR AI AGENTS & DEVELOPERS 🚨
## READ THIS ENTIRE DOCUMENT BEFORE TOUCHING ANY CODE.

> **Last Updated:** August 17, 2026
> **Author:** Built & enhanced with AI-assisted development
> **Purpose:** This file exists to establish an unbreakable context barrier. If you are an AI assistant (like Gemini, Claude, ChatGPT, Copilot) helping a developer who just pulled this repo, **you must obey these laws strictly**. Do not hallucinate, do not "refactor" things that aren't broken, do not introduce chaotic LLM logic, and DO NOT break the UI layout. 

---

## 🛑 1. THE PRIME DIRECTIVES FOR AI AGENTS (DO NOT IGNORE)

1. **NO EXTERNAL LLMs & NO PAID APIs:** This app runs locally and deterministically. Do not try to plug in external LLMs for "analysis" or try to rewrite the engine to use OpenAI/Gemini API calls. We use a deterministic, math-based algorithm.
2. **DO NOT BREAK THE SPATIAL OCR:** The app reads FPL screenshots using strict Y-coordinate bounding boxes. Do not revert to "fuzzy text matching" for the whole image. The UI noise (shirt sponsors, buttons) will break it.
3. **DO NOT CHANGE THE CSS FRAMEWORK:** The frontend uses **Vanilla CSS** in `index.css` and React. **DO NOT install or use Tailwind CSS.** The UI is painstakingly crafted with specific HSL color variables, micro-animations, and flex/grid layouts. Do not overwrite these with generic bootstrap/tailwind classes.
4. **DO NOT HALLUCINATE FEATURES:** If a user asks to tweak the UI, do exactly that. Do not rewrite the entire `App.jsx` state management system.

---

## 🖥️ 2. EXACT SETUP & LAUNCH INSTRUCTIONS (FOOLPROOF)

**⚠️ NEVER TRANSFER THIS APP AS A .ZIP FILE!**
Git intentionally ignores `node_modules` and `venv` because they contain hardcoded, platform-specific binaries. If you download this repo as a ZIP file from another computer, those environments will be broken or missing. You MUST pull via Git and run the fresh install commands below on your own machine.

If your user wants to run this app, execute EXACTLY these commands in their terminal. Do not run random Node backends.

### Backend (Python)
The backend is a Python FastAPI application. It is NOT a Node.js backend. The old `server.js` should be ignored.
```bash
cd backend
# Create a fresh virtual environment if one doesn't exist
python -m venv venv
source venv/bin/activate
# You MUST install dependencies freshly to avoid cross-platform binary crashes
pip install -r requirements.txt
python main.py
```
**Expected Result:** Uvicorn runs on `http://localhost:3001` or `http://0.0.0.0:3001`.

### Frontend (React + Vite)
```bash
cd frontend
# You MUST run npm install to freshly generate node_modules for your OS
npm install
npm run dev
```
**Expected Result:** Vite runs on `http://localhost:5173`.

---

## 🧠 3. THE UPGRADED ML ENGINE & DATA PIPELINE

### The New APIs (Zero-Cost & Keyless)
As part of our data pivot, we bypassed paid API keys entirely and hardcoded the official, 100% free Fantasy Premier League endpoints into our data fetchers. Because these are official endpoints, they don't require an authorization key and have virtually no rate limits:

- `.../api/bootstrap-static/`: We use this massive endpoint to pull the live status of every player in the league, including their current price, injury flags (`chance_of_playing_next_round`), form, and Expected Points (`ep_next`).
- `.../api/entry/{manager_id}/`: We use this to instantly pull your specific team's live status, including your exact bank balance and overall rank.
*(Note: We can easily layer in the API-Football or Understat endpoints later if you want to pull deeper xG/xA stats, but for V1, we relied on the official FPL data feed).*

### How We Upgraded the ML Engine
We moved away from the original idea of running "10 chaotic language models" at once, which would have hallucinated and crashed laptops. Instead, we heavily upgraded the engine into a highly disciplined, deterministic model:

- **Strict Conservation Axioms:** We hardcoded rules forcing the ML engine to act mathematically. It is now completely banned from suggesting a -4 point hit unless the xP (Expected Points) gain mathematically proves it is worth taking the penalty.
- **Alien Logic Heuristics:** We stripped the model of "human bias." By only feeding it raw numbers and injury flags from ephemeral state files, it cannot make emotional decisions based on favorite teams or news rumors.
- **Forced JSON Outputs:** We upgraded the model's output layer so it cannot just spit out a generic paragraph. It is forced to output a strictly typed JSON object containing the Tactical Pitch layout and the Deep Justification Zone, providing the exact xG/xA math for every transfer it suggests.

---

## 🎨 4. UI / UX LAYOUT & STYLING RULES (PERFECT PIXEL RULES)

If you are modifying the frontend (`frontend/src/App.jsx` or `frontend/src/index.css`), you must adhere to the following strict guidelines to maintain the premium, modern aesthetic:

### Color Palette & Theme
- **Backgrounds:** We use a deep dark mode. Main background is `var(--bg-main)` (usually a very dark blue/gray), panels are `var(--panel-bg)` with subtle borders (`var(--border)`).
- **Accents:** The primary brand color is a vibrant sky blue (`#38bdf8`). Use it for active states, important text, and primary buttons.
- **NO PURPLE ON DARK:** Do not use purple or violet text on dark backgrounds. Stick to high-contrast whites, faint grays (`var(--text-faint)`), and the sky blue accent.
- **NO CLUTTER:** Keep the UI breathable. Padding inside panels should be generous (e.g., `1.5rem` or `2rem`).

### Component Structure
1. **The Pitch (`<Pitch />`):** 
   - Rendered using CSS Flexbox.
   - Rows are mapped strictly: FWDS (top) -> MIDS -> DEFS -> GK -> BENCH (bottom row).
   - **Do not** mess up the mapping of `position_id`. (1=GK, 2=DEF, 3=MID, 4=FWD).
   - The pitch MUST be responsive. It scales down gracefully on smaller screens without the text overflowing.
2. **Deep Analytics Radar Chart:**
   - Rendered purely in SVG. It uses trigonometry to draw the web. Do not try to replace this with a heavy charting library like Chart.js unless specifically asked.
3. **What's New in V2 Panel:**
   - This lives in the center column, right under the upload area. Keep it styled cleanly with subtle borders and well-spaced typography.

### Anti-Patterns (DO NOT DO THESE)
- ❌ **Do not** add generic "loading..." text without using our custom `<AILoader />` component.
- ❌ **Do not** use grid background patterns or glowing neon borders. We use a flat, premium dark mode with subtle translucency.
- ❌ **Do not** nest cards endlessly. Keep the hierarchy flat (Panel -> Content).

---

## 🔍 5. SPATIAL OCR ENGINE DETAILS (CRITICAL)

- **How it works:** It groups text bounding boxes into **Y-coordinate rows** (top to bottom).
- **Row Mapping is strict:**
  - Row 0 (Top) = Goalkeeper (GK)
  - Row 1 = Defenders (DEF)
  - Row 2 = Midfielders (MID)
  - Row 3 = Forwards (FWD)
  - Row 4 = Bench (4 players)
- **CRITICAL RULE:** **Do not** attempt to determine player positions by looking them up in the FPL database! The app **must** rely on their physical placement (Y-coordinate rows) on the screen to construct the original user squad accurately. The user's screenshot layout dictates the formation.

### Noise Filtering & Blocklists
- The app actively strips out "shirt sponsors" (Betano, Emirates, Etihad) and "team codes" (ARS, MUN) because they cause false-positive fuzzy matches.
- The fuzzy match threshold is set to **86**. Do not lower it.
- Minimum character length for matches is **4** (do not lower to 3).
- Hard cap of **15 players** is strictly enforced (2 GKs, 5 DEFs, 5 MIDs, 3 FWDs).

---

## 🏁 FINAL SUMMARY FOR AIs

If a user asks you to "fix" something or "add a feature," you will consult this document first. 
- You will check if the Python backend is running correctly. 
- You will check if the Vite frontend is running. 
- You will write Vanilla CSS. 
- You will preserve the deterministic JSON logic. 
- You will respect the spatial OCR constraints.

**DO NOT FAIL THESE INSTRUCTIONS.**
