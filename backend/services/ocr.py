"""
==========================================================================
  SPATIAL OCR ENGINE FOR FPL SCREENSHOTS
==========================================================================
  This engine reads FPL team screenshots by analyzing the SPATIAL LAYOUT
  of the image, not just extracting random text.

  FPL pitch screenshots always follow this strict top-to-bottom order:
    ┌──────────────────────────────────────────────────────┐
    │  POWERUPS ROW: Bench Boost | Triple Captain | ...    │
    │  (with "Available" / "Unavailable" below each)       │
    ├──────────────────────────────────────────────────────┤
    │  PITCH ROW 0 (top):    GK       → always 1 player   │
    │  PITCH ROW 1:          DEF      → 3, 4, or 5        │
    │  PITCH ROW 2:          MID      → 2, 3, 4, or 5     │
    │  PITCH ROW 3 (bottom): FWD      → 1, 2, or 3        │
    ├──────────────────────────────────────────────────────┤
    │  BENCH ROW:  4 players (any positions)               │
    └──────────────────────────────────────────────────────┘

  The formation is detected by counting how many players appear in each
  row. For example, if Row 1 has 3 players, Row 2 has 4, Row 3 has 3,
  the detected formation is 3-4-3.

  Positions are assigned from WHERE the player sits on screen, NOT from
  the FPL database. This prevents mismatches when a player is listed as
  a MID in FPL but played as a FWD, etc.
==========================================================================
"""

import threading
import re
import cv2
import numpy as np
import easyocr
from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple, Optional


class OCREngine:
    """
    Spatially-aware OCR engine for FPL pitch screenshots.
    Reads player positions from their visual location on the pitch image.
    """

    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        self.lock = threading.Lock()

    # ──────────────────────────────────────────────────────────────────
    # IMAGE PREPROCESSING
    # ──────────────────────────────────────────────────────────────────
    def _preprocess(self, image_bytes: bytes):
        """
        Convert raw image bytes into a preprocessed grayscale image
        optimized for OCR text extraction.
        Pipeline: Decode → Grayscale → 2x Upscale → CLAHE → Gaussian Blur
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception("INVALID_IMAGE")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Upscale 2x — makes small player name text much clearer for OCR
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Dramatically improves contrast on the green pitch background
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Light Gaussian blur to smooth out high-frequency noise
        return cv2.GaussianBlur(enhanced, (3, 3), 0)

    # ──────────────────────────────────────────────────────────────────
    # Y-COORDINATE ROW CLUSTERING
    # ──────────────────────────────────────────────────────────────────
    def _cluster_into_rows(self, items: List[Dict], y_gap_threshold: int = 80) -> List[List[Dict]]:
        """
        Groups OCR items into horizontal rows based on Y-coordinate proximity.

        Two items are in the same row if their Y-centers are within
        y_gap_threshold pixels of each other.

        Returns: List of rows (top → bottom), each row sorted left → right.

        Example with y_gap_threshold=80:
          Item A at y=100, Item B at y=110 → same row
          Item C at y=300 → different row
        """
        if not items:
            return []

        sorted_items = sorted(items, key=lambda x: x['y'])

        rows = []
        current_row = [sorted_items[0]]

        for item in sorted_items[1:]:
            # Compare against the average Y of the current row for stability
            avg_y = sum(i['y'] for i in current_row) / len(current_row)
            if abs(item['y'] - avg_y) < y_gap_threshold:
                current_row.append(item)
            else:
                # Gap detected — start a new row
                rows.append(sorted(current_row, key=lambda x: x['x']))
                current_row = [item]

        # Don't forget the last row
        if current_row:
            rows.append(sorted(current_row, key=lambda x: x['x']))

        return rows

    # ──────────────────────────────────────────────────────────────────
    # MAIN IMAGE PROCESSING
    # ──────────────────────────────────────────────────────────────────
    def process_image(self, image_bytes: bytes) -> Tuple[List[Dict], List[str]]:
        """
        Run OCR on the FPL screenshot and return:
          - candidate_items: list of dicts with spatial coordinates
                             { clean_text, y, x, conf, raw_text }
          - powerups: list of detected powerup keyword strings

        This method does NOT match players yet — it only extracts and
        filters text candidates with their spatial positions preserved.
        """
        processed_img = self._preprocess(image_bytes)

        with self.lock:
            results = self.reader.readtext(
                processed_img,
                detail=1,
                paragraph=False,
                mag_ratio=1.5
            )

        # ── Build structured items with XY coordinates ──
        all_items = []
        for (bbox, text, conf) in results:
            y_center = (bbox[0][1] + bbox[2][1]) / 2.0
            x_center = (bbox[0][0] + bbox[1][0]) / 2.0
            all_items.append({
                'raw_text': text,
                'y': y_center,
                'x': x_center,
                'conf': conf,
            })

        candidate_items, detected_powerups = self._filter_items(all_items)
        # (Removed captaincy detection as it is now gracefully handled via points projection)

        return candidate_items, detected_powerups

    def _filter_items(self, all_items: List[Dict]) -> Tuple[List[Dict], List[str]]:
        # ── Detect Powerups from raw OCR text ──
        powerup_keywords = ["Wildcard", "Bench Boost", "Triple Captain", "Free Hit"]
        detected_powerups = []
        for item in all_items:
            for kw in powerup_keywords:
                if fuzz.partial_ratio(kw.lower(), item['raw_text'].lower()) > 85:
                    if kw not in detected_powerups:
                        detected_powerups.append(kw)

        # ── Filter out NON-PLAYER text (UI elements, fixtures, labels) ──
        # These are the words that appear on the FPL screenshot but are
        # NOT player names — they would cause false positive matches.
        ignore_words = [
            "AVAILABLE", "UNAVAILABLE", "WILDCARD", "BENCH BOOST",
            "TRIPLE CAPTAIN", "FREE HIT", "PITCH", "LIST",
            "GAMEWEEK", "DEADLINE", "POINTS", "CAPTAIN",
        ]

        # All 20 Premier League 3-letter team codes — these appear as
        # fixture text on the pitch and would otherwise fuzzy-match to
        # short player names like "Tel", "Son", "Eze", etc.
        team_codes = {
            "ARS", "AVL", "BOU", "BRE", "BHA", "BUR", "CHE", "CRY",
            "EVE", "FUL", "IPS", "LEI", "LIV", "MCI", "MUN", "NEW",
            "NFO", "SOU", "TOT", "WHU", "WOL", "HUL", "COV", "LEE",
            "SHU", "LUT", "PLY", "SUN", "BIR", "WBA", "MID", "NOR",
        }

        # Shirt sponsor & kit manufacturer names that appear on jerseys.
        # "Betano" on Martinez's jersey was being matched to "Beto"!
        sponsor_names = {
            "BETANO", "EMIRATES", "ETIHAD", "ADIDAS", "NIKE", "PUMA",
            "CASTORE", "UMBRO", "MACRON", "HUMMEL", "JOMA", "KAPPA",
            "SPORTSBET", "SPORTBET", "THREE", "STAKE", "AIA",
            "VISIT", "RWANDA", "CINCH", "TEAMVIEWER", "SAMSUNG",
        }

        candidate_items = []
        for item in all_items:
            raw_upper = item['raw_text'].upper().strip()

            # Skip fixture tags like "BHA (A)" or "MCI (H)"
            if "(H)" in raw_upper or "(A)" in raw_upper:
                continue

            # Skip known UI / navigation text
            if any(w in raw_upper for w in ignore_words):
                continue

            # Skip 3-letter team codes ("COV", "BOU", "FUL", etc.)
            stripped = raw_upper.strip()
            if stripped in team_codes:
                continue

            # Skip single-character labels and position tags
            if stripped in ("GK", "DEF", "MID", "FWD", "V", "C"):
                continue

            # Skip shirt sponsor / kit manufacturer names
            if stripped in sponsor_names:
                continue

            # ── Clean text for fuzzy matching ──
            # Common OCR misreads on the FPL green pitch background:
            #   1 → l, 0 → o, 5 → s, 8 → B
            clean = item['raw_text']
            clean = clean.replace('1', 'l').replace('0', 'o')
            clean = clean.replace('5', 's').replace('8', 'B')
            clean = re.sub(r'[^a-zA-ZÀ-ÿ\s\-\.]', '', clean).strip()

            # Require at least 4 characters to avoid matching junk
            # 3-letter texts (team codes that slipped through, stray OCR)
            if len(clean) > 3:
                item['clean_text'] = clean
                candidate_items.append(item)

        return candidate_items, detected_powerups


    # ──────────────────────────────────────────────────────────────────
    # SPATIAL PLAYER MATCHING  (the core of the new engine)
    # ──────────────────────────────────────────────────────────────────
    def match_players_spatial(
        self,
        candidates: List[Dict],
        fpl_players: List[Dict]
    ) -> Dict:
        """
        Match OCR candidate texts to FPL players using SPATIAL ROW ANALYSIS.

        Instead of guessing positions from the FPL database, this method:
          1. Fuzzy-matches each OCR text to an FPL player name
          2. Clusters matched items into rows by Y-coordinate
          3. Assigns positions based on row order:
               Row 0 → GK  (position_id = 1)
               Row 1 → DEF (position_id = 2)
               Row 2 → MID (position_id = 3)
               Row 3 → FWD (position_id = 4)
               Row 4+ → Bench
          4. Derives the formation from the count of players per row

        Returns dict:
          {
            'starters':   List[Dict]  — 11 players with correct element_type
            'bench':      List[Dict]  — 4 bench players
            'formation':  str         — e.g. "3-4-3"
            'row_counts': List[int]   — players per row [1, 3, 4, 3]
          }
        """
        player_names = [p['web_name'] for p in fpl_players]

        # ── Step 1: Fuzzy-match each candidate to an FPL player ──
        matched_items = []
        used_ids = set()

        for item in candidates:
            match = process.extractOne(
                item['clean_text'],
                player_names,
                scorer=fuzz.WRatio
            )
            # Threshold of 86 prevents noise text from matching real players.
            # "Betano" → "Beto" scores ~78, so 86 kills it cleanly.
            # Real player names like "B.Fernandes" still score 90+.
            if match and match[1] > 86:
                for p in fpl_players:
                    if p['web_name'] == match[0] and p['id'] not in used_ids:
                        item['player'] = p.copy()
                        item['match_score'] = match[1]
                        matched_items.append(item)
                        used_ids.add(p['id'])
                        break

        # ── Safety cap: An FPL team has exactly 15 players (11 + 4 bench).
        # If noise slipped through, keep only the top 15 by match score.
        if len(matched_items) > 15:
            matched_items.sort(key=lambda x: x['match_score'], reverse=True)
            matched_items = matched_items[:15]

        # ── Step 2: Cluster matched items into spatial rows ──
        # y_gap_threshold=80 works well on 2x upscaled FPL screenshots
        # where pitch rows are ~150-200px apart vertically
        rows = self._cluster_into_rows(matched_items, y_gap_threshold=80)

        # ── Step 3: Assign positions from row order ──
        # The FPL pitch ALWAYS renders top-to-bottom: GK → DEF → MID → FWD
        # So we map row index to position_id directly
        POSITION_MAP = {
            0: 1,  # Row 0 = GK
            1: 2,  # Row 1 = DEF
            2: 3,  # Row 2 = MID
            3: 4,  # Row 3 = FWD
        }

        starters = []
        bench = []
        row_counts = []

        for row_idx, row in enumerate(rows):
            if row_idx <= 3:
                # ── Starting XI: position from spatial location ──
                pos_id = POSITION_MAP[row_idx]
                row_counts.append(len(row))
                for item in row:
                    player = item['player'].copy()
                    # OVERRIDE the FPL database position with the spatial one
                    player['element_type'] = pos_id
                    starters.append(player)
            else:
                # ── Bench: all remaining rows below the pitch ──
                for item in row:
                    player = item['player'].copy()
                    bench.append(player)

        # ── Step 4: Derive formation string (DEF-MID-FWD) ──
        if len(row_counts) >= 4:
            formation = f"{row_counts[1]}-{row_counts[2]}-{row_counts[3]}"
        elif len(row_counts) == 3:
            # Edge case: only 3 rows detected (maybe GK merged with DEF)
            formation = f"{row_counts[0]}-{row_counts[1]}-{row_counts[2]}"
        else:
            formation = "4-4-2"  # Safe fallback

        return {
            'starters': starters,
            'bench': bench,
            'formation': formation,
            'row_counts': row_counts,
        }

    # ──────────────────────────────────────────────────────────────────
    # LEGACY INTERFACE (kept for backward compatibility)
    # ──────────────────────────────────────────────────────────────────
    def match_players(self, extracted_texts: List[str], fpl_players: List[Dict]) -> List[Dict]:
        """Legacy flat matching — use match_players_spatial instead."""
        player_names_list = [p['web_name'] for p in fpl_players]
        matched_players = []
        used_ids = set()

        for clean_text in extracted_texts:
            if isinstance(clean_text, dict):
                clean_text = clean_text.get('clean_text', '')
            match = process.extractOne(clean_text, player_names_list, scorer=fuzz.WRatio)
            if match and match[1] > 75:
                for p in fpl_players:
                    if p['web_name'] == match[0] and p['id'] not in used_ids:
                        matched_players.append(p)
                        used_ids.add(p['id'])
                        break

        return matched_players


# ── Singleton instance ──
ocr_service = OCREngine()
