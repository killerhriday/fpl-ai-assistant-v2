import sys, os, cv2
import numpy as np
sys.path.append(os.path.join(os.getcwd()))
from services.ocr import ocr_service

img = cv2.imread('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/.user_uploaded/media_1786652535214.jpg')

# Process the whole image
res = ocr_service.reader.readtext(img, text_threshold=0.3, low_text=0.3)

for bbox, text, conf in res:
    if text.strip().upper() in ['C', 'V', '(C)', '(V)']:
        print(f"Found {text} at {bbox[0]}")
