import threading
import cv2
import numpy as np
import easyocr
import time
from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple

class OCREngine:
    def __init__(self):
        # The reader takes some time to initialize
        self.reader = easyocr.Reader(['en'])
        self.lock = threading.Lock()

    def process_image(self, image_bytes: bytes) -> Tuple[List[str], List[str]]:
        import re
        # Decodes image directly from memory
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception("INVALID_IMAGE")
            
        # --- Preprocessing for better OCR ---
        # 1. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 2. Resize image (upscale by 2x) to make text clearer
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # 3. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        # 4. Slight blur to remove high-frequency noise
        processed_img = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
        with self.lock:
            # Add mag_ratio to let EasyOCR magnify internally as well, and use standard constraints
            results = self.reader.readtext(processed_img, detail=1, paragraph=False, mag_ratio=1.5)
            
        # Sort top-to-bottom (grouped into rows by rounding Y to nearest 40px), then left-to-right
        results.sort(key=lambda x: (round(x[0][0][1] / 40) * 40, x[0][0][0]))
        
        extracted_texts = []
        
        # Strings that we should completely ignore to prevent false positives
        ignore_words = [
            "AVAILABLE", "UNAVAILABLE", "WILDCARD", "BENCH BOOST", 
            "TRIPLE CAPTAIN", "FREE HIT", "PITCH", "LIST", "GAMEWEEK", "DEADLINE",
            "GK", "DEF", "MID", "FWD"
        ]
        
        for res in results:
            raw_text = res[1]
            raw_upper = raw_text.upper()
            
            # Ignore fixture tags like BHA (A) or MCI (H)
            if "(H)" in raw_upper or "(A)" in raw_upper:
                continue
                
            # Ignore known UI text
            if any(word in raw_upper for word in ignore_words):
                continue
                
            # Advanced cleaning for FPL names
            text = raw_text.replace('1', 'l').replace('0', 'o').replace('5', 's').replace('8', 'B')
            text = re.sub(r'[^a-zA-ZÀ-ÿ\s\-]', '', text).strip()
            if len(text) > 2:
                extracted_texts.append(text)
        
        # Powerups
        powerup_keywords = ["Wildcard", "Bench Boost", "Triple Captain", "Free Hit"]
        detected_powerups = []
        for res in results: # check original text for powerups
            for kw in powerup_keywords:
                if fuzz.partial_ratio(kw.lower(), res[1].lower()) > 85:
                    if kw not in detected_powerups:
                        detected_powerups.append(kw)
                        
        return extracted_texts, detected_powerups

    def match_players(self, extracted_texts: List[str], fpl_players: List[Dict]) -> List[Dict]:
        player_names_list = [p['web_name'] for p in fpl_players]
        matched_players = []
        used_ids = set()
        
        for clean_text in extracted_texts:
            match = process.extractOne(clean_text, player_names_list, scorer=fuzz.WRatio)
            # Increased threshold to 82 to eliminate random UI text matching players
            if match and match[1] > 82:  
                for p in fpl_players:
                    if p['web_name'] == match[0] and p['id'] not in used_ids:
                        matched_players.append(p)
                        used_ids.add(p['id'])
                        break
                        
        return matched_players

ocr_service = OCREngine()
