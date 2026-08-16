import sys, os, cv2
import numpy as np
sys.path.append(os.path.join(os.getcwd()))
from services.ocr import ocr_service

img = cv2.imread('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/.user_uploaded/media_1786652535214.jpg')

with open('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/.user_uploaded/media_1786652535214.jpg', 'rb') as f:
    items, _ = ocr_service.process_image(f.read())

for item in items:
    name = item['clean_text']
    y = int(item['y'] / 2.0)
    x = int(item['x'] / 2.0)
    if name == 'Haaland':
        crop = img[max(0, y-100):min(img.shape[0], y+20), max(0, x-100):min(img.shape[1], x+100)]
        cv2.imwrite('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/Haaland_full_shirt.jpg', crop)
