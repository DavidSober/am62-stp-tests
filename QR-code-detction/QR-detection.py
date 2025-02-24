import cv2
import numpy as np
import os
from pyzbar.pyzbar import decode
from datetime import datetime

# Ensure the "qr-images" directory exists
QR_IMAGE_DIR = "qr-images"
os.makedirs(QR_IMAGE_DIR, exist_ok=True)

# Open the camera (/dev/video0) with Video4Linux2 (V4L2)
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Set format
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height

if not cap.isOpened():
    print("Error: Could not open /dev/video0")
    exit()

print("QR Code Scanner is running. Press Ctrl+C to stop.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from /dev/video0")
            break

        # Convert frame to grayscale (optional, improves QR detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect QR codes
        decoded_objects = decode(gray)

        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            print(f"Detected QR Code: {qr_data}")

            # Save the frame when a QR code is detected
            filename = os.path.join(QR_IMAGE_DIR, f"qr_detected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            cv2.imwrite(filename, frame)
            print(f"Saved image: {filename}")

except KeyboardInterrupt:
    print("\nStopping QR detection...")

finally:
    cap.release()
    print("Camera released. Exiting.")
