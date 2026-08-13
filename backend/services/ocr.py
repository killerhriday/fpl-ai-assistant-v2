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
        # Decodes image directly from memory
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception("INVALID_IMAGE")
            
        with self.lock:
            results = self.reader.readtext(img)
            
        # Sort top-to-bottom
        results.sort(key=lambda x: x[0][0][1])
        extracted_texts = [res[1] for res in results if len(res[1]) > 2]
        
        # Powerups
        powerup_keywords = ["Wildcard", "Bench Boost", "Triple Captain", "Free Hit"]
        detected_powerups = []
        for text in extracted_texts:
            for kw in powerup_keywords:
                if fuzz.partial_ratio(kw.lower(), text.lower()) > 85:
                    if kw not in detected_powerups:
                        detected_powerups.append(kw)
                        
        return extracted_texts, detected_powerups

    def match_players(self, extracted_texts: List[str], fpl_players: List[Dict]) -> List[Dict]:
        player_names_list = [p['web_name'] for p in fpl_players]
        matched_players = []
        used_ids = set()
        
        for text in extracted_texts:
            clean_text = text.replace('1', 'l').replace('0', 'o')
            match = process.extractOne(clean_text, player_names_list, scorer=fuzz.WRatio)
            if match and match[1] > 65:  
                for p in fpl_players:
                    if p['web_name'] == match[0] and p['id'] not in used_ids:
                        matched_players.append(p)
                        used_ids.add(p['id'])
                        break
                        
        return matched_players

ocr_service = OCREngine()
