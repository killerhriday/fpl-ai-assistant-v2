import sys, os, cv2
import numpy as np
sys.path.append(os.path.join(os.getcwd()))
from services.ocr import ocr_service

img = cv2.imread('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/.user_uploaded/media_1786652535214.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

with open('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/.user_uploaded/media_1786652535214.jpg', 'rb') as f:
    items, _ = ocr_service.process_image(f.read())

scores = []
for item in items:
    name = item['clean_text']
    y = int(item['y'] / 2.0)
    x = int(item['x'] / 2.0)
    crop = gray[max(0, y-75):min(gray.shape[0], y-35), max(0, x-35):min(gray.shape[1], x+5)]
    
    # We want a high number of very dark pixels AND a reasonable number of very white pixels (the C or V)
    dark = np.sum(crop < 50)
    white = np.sum(crop > 220)
    
    # We can multiply them or just add them (since both need to be present)
    score = min(dark, white * 3) # white pixels are fewer than dark ones in a badge
    print(f"{name}: dark={dark}, white={white}, score={score}")
    scores.append((score, name))

scores.sort(reverse=True)
print("Top candidates:", scores[:5])
