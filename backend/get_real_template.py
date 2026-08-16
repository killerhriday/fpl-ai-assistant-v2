import sys, os, cv2
import numpy as np

img = cv2.imread('/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/Haaland_full_shirt.jpg')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The badge is likely the darkest spot on the top left.
# Let's just find all dark blobs.
_, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for i, cnt in enumerate(contours):
    x, y, w, h = cv2.boundingRect(cnt)
    # Badge is usually small (e.g., 10x10 to 30x30)
    if 10 < w < 30 and 10 < h < 30:
        crop = img[y:y+h, x:x+w]
        cv2.imwrite(f'/Users/hridaypatel/.gemini/antigravity/brain/5aa7708a-6bed-46b3-92fd-87ce74d29974/blob_{i}.jpg', crop)
