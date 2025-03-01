import cv2
import os
import threading
import sys
from datetime import datetime
import time

# Check for command-line arguments
show_video = len(sys.argv) > 1 and sys.argv[1] == "v"


print("add v arg if you want to display video")
time.sleep(1)

# Ensure the "face-images" directory exists
output_dir = "face-images"
os.makedirs(output_dir, exist_ok=True)

# Open the camera (/dev/video0) with Video4Linux2 (V4L2)
cap = cv2.VideoCapture(4, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Set format
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height
cap.set(cv2.CAP_PROP_FPS, 30)  # Try to force max FPS

if not cap.isOpened():
    print("Error: Could not open /dev/video0")
    exit()

print("Face detection running. Press Ctrl+C to stop.")

# Load Haar cascade
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface.xml")

# Time tracking variables
previous_time = datetime.now()
deltas = []  # Stores last 50 frame deltas
frame_counter = 0  # Counter for processing logic
save_counter = 1  # Counter for saving face images

# Function to save images asynchronously
def save_image(image, filename):
    cv2.imwrite(filename, image)

try:
    while True:
        # T1 - Start time
        current_time = datetime.now()

        # Capture a frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from /dev/video0")
            break

        # Resize frame for faster face detection
        small_frame = cv2.resize(frame, (320, 240))

        # Convert to grayscale (Haar cascades work better in grayscale)
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

        detected = False  # Flag to indicate face detection
        for (x, y, w, h) in faces:
            detected = True

            # Draw rectangle around detected face (only if video display is enabled)
            if show_video:
                cv2.rectangle(frame, (x * 2, y * 2), ((x + w) * 2, (y + h) * 2), (0, 255, 0), 2)

        # If a face is detected, print message and save every 5th frame
        if detected:
            print("Found face!")

            if frame_counter % 5 == 0:
                filename = os.path.join(output_dir, f"face_detected_{save_counter}.jpg")
                threading.Thread(target=save_image, args=(frame, filename)).start()
                print(f"Saved image: {filename}")
                save_counter += 1  # Increment save counter

        # Display video if "v" argument was provided
        if show_video:
            cv2.imshow("Camera Feed", frame)
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
        frame_counter += 1
        if frame_counter % 5 == 0 and len(deltas) >= 50:
            avg_delta = sum(deltas) / len(deltas)
            avg_fps = 1 / avg_delta if avg_delta > 0 else 0
            print(f"🔹 [Avg FPS over last 50 frames: {avg_fps:.2f}]")

except KeyboardInterrupt:
    print("\nStopping detection...")

finally:
    cap.release()  # Release the camera
    cv2.destroyAllWindows()
