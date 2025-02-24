import cv2
import os

# Ensure the "face-images" directory exists
output_dir = "face-images"
os.makedirs(output_dir, exist_ok=True)

# Open the camera (/dev/video0) with Video4Linux2 (V4L2)
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Set format
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height

if not cap.isOpened():
    print("Error: Could not open /dev/video0")
    exit()

print("Press Ctrl+C to stop.")

# Load Haar cascade
face_cascade = cv2.CascadeClassifier("haarcascade_frontalface.xml")

frame_counter = 0  # Counter to control frame saving
save_counter = 1  # Counter for saving face images

try:
    while True:
        # Capture a frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from /dev/video0")
            break

        # Convert to grayscale (Haar cascades work better in grayscale)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))

        detected = False  # Flag to indicate face detection
        for (x, y, w, h) in faces:
            detected = True

        # If a face is detected, print message and save every 5th frame
        if detected:
            print("Found face!")

            if frame_counter % 5 == 0:
                filename = os.path.join(output_dir, f"face_detected_{save_counter}.jpg")
                cv2.imwrite(filename, frame)
                print(f"Saved image: {filename}")
                save_counter += 1  # Increment save counter

        frame_counter += 1  # Increment frame counter

except KeyboardInterrupt:
    print("\nStopping detection...")

finally:
    cap.release()  # Release the camera
    cv2.destroyAllWindows()
