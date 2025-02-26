import cv2
import numpy as np
import os
import threading
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
cap.set(cv2.CAP_PROP_FPS, 30)  # Try to force max FPS

if not cap.isOpened():
    print("Error: Could not open /dev/video0")
    exit()

print("QR Code Scanner is running. Press Ctrl+C to stop.")

# Time tracking variables
previous_time = datetime.now()
deltas = []  # Stores the last 50 frame deltas
frame_count = 0  # Track number of frames

# Function to save images asynchronously
# Saving image reduces fps by 5
def save_image(image, filename):
    cv2.imwrite(filename, image)

try:
    while True:
        # T1 - Start time
        current_time = datetime.now()

        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from /dev/video0")
            break


        # Resize frame to reduce QR processing time
        small_frame = cv2.resize(frame, (320, 240)) # 240p is 30 fps
        #small_frame = frame # keeps it at 480p
  

        # Convert frame to grayscale (comment this out to test if color QR detection is faster)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # Detect QR codes
        decoded_objects = decode(gray)

        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            print(f"Detected QR Code: {qr_data}")

            # Save the frame asynchronously when a QR code is detected
            filename = os.path.join(QR_IMAGE_DIR, f"qr_detected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            #threading.Thread(target=save_image, args=(frame, filename)).start() # 5 fps hit
            print(f"Saved image: {filename}")

        # T2 - Compute time delta
        time_delta = (current_time - previous_time).total_seconds()  # Time between frames
        previous_time = current_time  # Update previous timestamp

        # Store delta in list (keep only last 50)
        deltas.append(time_delta)
        if len(deltas) > 50:
            deltas.pop(0)

        # Compute FPS from delta
        fps = 1 / time_delta if time_delta > 0 else 0
        print(f"Frame Time: {time_delta:.4f} sec | FPS: {fps:.2f}")

        # Every 5th frame, compute average FPS from last 50 deltas
        frame_count += 1
        if frame_count % 5 == 0 and len(deltas) >= 50:
            avg_delta = sum(deltas) / len(deltas)
            avg_fps = 1 / avg_delta if avg_delta > 0 else 0
            print(f"🔹 [Avg FPS over last 50 frames: {avg_fps:.2f}]")

except KeyboardInterrupt:
    print("\nStopping QR detection...")

finally:
    cap.release()
    print("Camera released. Exiting.")
