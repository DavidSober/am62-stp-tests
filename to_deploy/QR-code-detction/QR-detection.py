import cv2
import numpy as np
import os
import threading
import sys
from pyzbar.pyzbar import decode
from datetime import datetime

# Check for command-line arguments
show_video = len(sys.argv) > 1 and sys.argv[1] == "v"

# Ensure the "qr-images" directory exists
QR_IMAGE_DIR = "qr-images"
os.makedirs(QR_IMAGE_DIR, exist_ok=True)

# Open the camera (/dev/video0) with Video4Linux2 (V4L2)
cap = cv2.VideoCapture(4, cv2.CAP_V4L2)
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
        small_frame = cv2.resize(frame, (320, 240))  # 240p is 30 FPS

        # Convert frame to grayscale for QR processing (comment out for color detection)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # Detect QR codes
        decoded_objects = decode(gray)

        for obj in decoded_objects:
            qr_data = obj.data.decode("utf-8")
            print(f"Detected QR Code: {qr_data}")

            # Save the frame asynchronously when a QR code is detected
            filename = os.path.join(QR_IMAGE_DIR, f"qr_detected_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            threading.Thread(target=save_image, args=(frame, filename)).start()  # 5 FPS hit
            print(f"Saved image: {filename}")

            # Draw a rectangle around detected QR codes (if video is enabled)
            if show_video:
                x, y, w, h = obj.rect
                cv2.rectangle(frame, (x * 2, y * 2), ((x + w) * 2, (y + h) * 2), (0, 255, 0), 2)

        # Display video if "v" argument was provided
        if show_video:
            cv2.imshow("QR Code Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

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
    cv2.destroyAllWindows()
    print("Camera released. Exiting.")
