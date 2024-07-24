import cv2
import numpy as np
import os

def calculate_iou(box1, box2):
    # Calculate intersection over union of two boxes
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    xi1, yi1 = max(x1, x2), max(y1, y2)
    xi2, yi2 = min(x1 + w1, x2 + w2), min(y1 + h1, y2 + h2)
    
    intersection_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - intersection_area
    
    iou = intersection_area / union_area if union_area > 0 else 0
    return iou

def segment_figures(image_path, output_folder):
    # Read the image
    img = cv2.imread(image_path)
    original_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

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

        # check if current box overlaps with any of the valid boxes
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
            
            #if calculate_iou(current_box, valid_box) > 0.5:  # Adjust this threshold as needed
            #    is_valid = False
            #    break
        
        if is_valid:
            valid_contours.append(contour)

    # Process valid contours
    #idx = 0
    for i, contour in enumerate(valid_contours):
        x, y, w, h = cv2.boundingRect(contour)

        # Add some padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2*padding)
        h = min(img.shape[0] - y, h + 2*padding)

        # Crop the figure
        figure = original_img[y:y+h, x:x+w]

        # Save the cropped figure
        output_path = os.path.join(output_folder, f"figure_{i+1}.png")
        cv2.imwrite(output_path, figure)

        # Draw rectangle on original image in red color
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)  # Red color (BGR format)

    # Save the annotated image with red bounding boxes
    annotated_path = os.path.join(output_folder, "annotated_red_boxes.png")
    cv2.imwrite(annotated_path, img)
# Usage
image_path = "./test_scripts/repina_1.png"
output_folder = "./test_scripts/output"
os.makedirs(output_folder, exist_ok=True)
segment_figures(image_path, output_folder)