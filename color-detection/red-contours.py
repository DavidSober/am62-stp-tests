import cv2
import numpy as np
import os

# Ensure the "color-images" directory exists
output_dir = "color-images"
os.makedirs(output_dir, exist_ok=True)

# Open the camera (/dev/video4)
cap = cv2.VideoCapture(4, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Set format
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height

if not cap.isOpened():
    print("Error: Could not open /dev/video4")
    exit()

print("Press Ctrl+C to stop.")

frame_counter = 0  # Counter to control frame saving

try:
    while True:
        # Capture a frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from /dev/video4")
            break

        # Convert to HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Define lower and upper bounds for detecting red color
        lower_red1 = np.array([0, 120, 70])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 70])
        upper_red2 = np.array([180, 255, 255])

        # Create masks for red color
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2  # Combine both masks

        # Find contours of red regions
        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected = False  # Flag to indicate red was detected
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1500:  # Adjust area threshold for filtering false positives
                detected = True
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw bounding box

        # If red was detected, print message and save image every 5th frame
        if detected:
            print("Red seen!")

            if frame_counter % 5 == 0:
                filename = os.path.join(output_dir, f"red_detected_{frame_counter}.jpg")
                cv2.imwrite(filename, frame)
                print(f"Saved image: {filename}")

                # Create a blank image for contour visualization
                contour_image = np.zeros_like(frame)  # Black image same size as frame
                cv2.drawContours(contour_image, contours, -1, (255, 255, 255), 2)  # White contours

                # Save the contour visualization
                contour_filename = os.path.join(output_dir, f"contours_{frame_counter}.jpg")
                cv2.imwrite(contour_filename, contour_image)
                print(f"Saved contour image: {contour_filename}")

        frame_counter += 1  # Increment frame counter

except KeyboardInterrupt:
    print("\nStopping detection...")

finally:
    cap.release()  # Release the camera
    cv2.destroyAllWindows()
