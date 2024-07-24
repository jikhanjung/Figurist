import cv2
import numpy as np
import os
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def find_nearest_text(box, texts):
    x, y, w, h = box
    center_x, center_y = x + w/2, y + h/2
    
    nearest_text = None
    min_distance = float('inf')
    
    for text in texts:
        text_x, text_y = text['box'][0], text['box'][1]
        distance = ((center_x - text_x)**2 + (center_y - text_y)**2)**0.5
        
        if distance < min_distance:
            min_distance = distance
            nearest_text = text['text']
    
    return nearest_text

def segment_figures(image_path, output_folder):
    # Read the image
    img = cv2.imread(image_path)
    original_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Perform OCR
    ocr_results = pytesseract.image_to_data(Image.fromarray(gray), output_type=pytesseract.Output.DICT)
    texts = []
    for i, text in enumerate(ocr_results['text']):
        if text.strip():
            x, y, w, h = ocr_results['left'][i], ocr_results['top'][i], ocr_results['width'][i], ocr_results['height'][i]
            texts.append({'text': text, 'box': (x, y, w, h)})

    # Apply threshold
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Sort contours by area (largest first)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    valid_contours = []
    for contour in contours:
        if cv2.contourArea(contour) < 1000:  # Adjust this value as needed
            continue
        
        x, y, w, h = cv2.boundingRect(contour)
        current_box = (x, y, w, h)
        
        # Check overlap with existing valid contours
        is_valid = True

        for valid_contour in valid_contours:
            vx, vy, vw, vh = cv2.boundingRect(valid_contour)
            valid_box = (vx, vy, vw, vh)

            # check if one is within the other
            if (vx <= x <= vx + vw or x <= vx <= x + w) and (vy <= y <= vy + vh or y <= vy <= y + h):
                is_valid = False
                break
            # check vice versa
            if (x <= vx <= x + w or vx <= x <= vx + vw) and (y <= vy <= y + h or vy <= y <= vy + vh):
                # remove the smaller box
                if w * h > vw * vh:
                    valid_contours.remove(valid_contour)
                else:
                    is_valid = False
                break
        
        if is_valid:
            valid_contours.append(contour)

    # Process valid contours
    for i, contour in enumerate(valid_contours):
        x, y, w, h = cv2.boundingRect(contour)

        # Add some padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2*padding)
        h = min(img.shape[0] - y, h + 2*padding)

        # Find nearest text
        nearest_text = find_nearest_text((x, y, w, h), texts)

        # Crop the figure
        figure = original_img[y:y+h, x:x+w]

        # Save the cropped figure
        output_path = os.path.join(output_folder, f"figure_{nearest_text or i+1}.png")
        cv2.imwrite(output_path, figure)

        # Draw rectangle on original image in red color
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)  # Red color (BGR format)

        # Put text on the image
        cv2.putText(img, nearest_text or str(i+1), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # Save the annotated image with red bounding boxes and text
    annotated_path = os.path.join(output_folder, "annotated_red_boxes_with_text.png")
    cv2.imwrite(annotated_path, img)

# Usage
image_path = "./test_scripts/Fig.08.png"
output_folder = "./test_scripts/output"
os.makedirs(output_folder, exist_ok=True)
segment_figures(image_path, output_folder)