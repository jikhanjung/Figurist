import cv2
import numpy as np
import os

def check_overlap(box1, box2):
    x1, y1, w1, h1 = box1[:4]
    x2, y2, w2, h2 = box2[:4]
    
    # Check if one box is inside the other
    if (x1 <= x2 <= x1 + w1 or x2 <= x1 <= x2 + w2) and (y1 <= y2 <= y1 + h1 or y2 <= y1 <= y2 + h2):
        return True
    return False

def segment_figures(image_path, output_folder):
    # Read the image
    img = cv2.imread(image_path)
    original_img = img.copy()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply threshold
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Get bounding boxes for all contours
    bounding_boxes = []
    for contour in contours:
        if cv2.contourArea(contour) < 1000:  # Adjust this value as needed
            continue
        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, w, h))

    # Remove overlapping boxes, keeping the larger ones
    valid_boxes = []
    for box in bounding_boxes:
        is_valid = True
        for valid_box in valid_boxes:
            if check_overlap(box, valid_box):
                if box[2] * box[3] > valid_box[2] * valid_box[3]:
                    valid_boxes.remove(valid_box)
                else:
                    is_valid = False
                break
        if is_valid:
            valid_boxes.append(box)

    if not valid_boxes:
        print("No valid boxes found.")
        return

    # Calculate average height of boxes
    avg_height = sum(box[3] for box in valid_boxes) / len(valid_boxes)

    # Assign row numbers based on y-coordinate and average height
    for i, box in enumerate(valid_boxes):
        box_y = box[1]
        row = int(box_y / (avg_height * 1.2))  # 1.2 is a factor to allow some variation
        valid_boxes[i] = box + (row,)  # Add row number as the 5th element of the tuple

    # Sort boxes first by row, then by x-coordinate
    valid_boxes.sort(key=lambda box: (box[4], box[0]))

    # Process valid boxes
    for i, (x, y, w, h, _) in enumerate(valid_boxes, start=1):
        # Add some padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(img.shape[1] - x, w + 2*padding)
        h = min(img.shape[0] - y, h + 2*padding)

        # Crop the figure
        figure = original_img[y:y+h, x:x+w]

        # Save the cropped figure
        output_path = os.path.join(output_folder, f"figure_{i}.png")
        cv2.imwrite(output_path, figure)

        # Draw rectangle on original image in red color
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)  # Red color (BGR format)

        # Put number on the image
        cv2.putText(img, str(i), (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # Save the annotated image with red bounding boxes and numbers
    annotated_path = os.path.join(output_folder, "annotated_red_boxes_with_numbers.png")
    cv2.imwrite(annotated_path, img)

# Usage
image_path = "./test_scripts/Fig.08.png"
output_folder = "./test_scripts/output"
os.makedirs(output_folder, exist_ok=True)
segment_figures(image_path, output_folder)