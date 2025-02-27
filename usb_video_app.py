import sys
import subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()

        self.gst_process = None  # Store the GStreamer process

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.connect_btn = QPushButton("Connect", self)
        self.connect_btn.clicked.connect(self.setup_usb_network)
        layout.addWidget(self.connect_btn)

        self.start_video_btn = QPushButton("Start Video", self)
        self.start_video_btn.clicked.connect(self.start_gstreamer)
        layout.addWidget(self.start_video_btn)

        self.stop_video_btn = QPushButton("Stop Video", self)
        self.stop_video_btn.clicked.connect(self.stop_gstreamer)
        layout.addWidget(self.stop_video_btn)

        self.setLayout(layout)
        self.setWindowTitle("USB Network & Video Stream")
        self.resize(300, 200)

    def setup_usb_network(self):
        """Runs the IP setup commands when 'Connect' is pressed."""
        commands = [
            ["sudo", "ip", "addr", "add", "192.168.2.1/24", "dev", "enx42ea74d29238"],
            ["sudo", "ip", "link", "set", "enx42ea74d29238", "up"]
        ]
        for cmd in commands:
            try:
                subprocess.run(cmd, check=True)
                print(f"Executed: {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                print(f"Error running command: {e}")

    def start_gstreamer(self):
        """Starts the GStreamer video stream."""
        if self.gst_process is None:
            gst_command = [
                "gst-launch-1.0", "udpsrc", "port=5000",
                "!", "application/x-rtp, encoding-name=JPEG, payload=26",
                "!", "rtpjpegdepay", "!", "jpegdec", "!", "autovideosink"
            ]
            self.gst_process = subprocess.Popen(gst_command)
            print("GStreamer started.")

    def stop_gstreamer(self):
        """Stops the GStreamer video stream."""
        if self.gst_process:
            self.gst_process.terminate()
            self.gst_process.wait()
            self.gst_process = None
            print("GStreamer stopped.")

    def closeEvent(self, event):
        """Ensure GStreamer stops when the app is closed."""
        self.stop_gstreamer()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoApp()
    window.show()
    sys.exit(app.exec())
