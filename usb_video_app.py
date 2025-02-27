import sys
import subprocess
import gi
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QThread

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

class VideoThread(QThread):
    """Runs a separate GStreamer loop to prevent Qt threading issues."""
    def run(self):
        loop = GLib.MainLoop()
        loop.run()

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()

        Gst.init(None)  # Initialize GStreamer in a separate thread
        self.gst_thread = VideoThread()
        self.gst_thread.start()

        self.initUI()
        self.pipeline = None
        self.appsink = None

    def initUI(self):
        layout = QVBoxLayout()

        # Re-adding "Connect" button
        self.connect_btn = QPushButton("Connect", self)
        self.connect_btn.clicked.connect(self.setup_usb_network)
        layout.addWidget(self.connect_btn)

        # Video Label to display stream
        self.video_label = QLabel(self)
        layout.addWidget(self.video_label)

        self.start_video_btn = QPushButton("Start Video", self)
        self.start_video_btn.clicked.connect(self.start_gstreamer)
        layout.addWidget(self.start_video_btn)

        self.stop_video_btn = QPushButton("Stop Video", self)
        self.stop_video_btn.clicked.connect(self.stop_gstreamer)
        layout.addWidget(self.stop_video_btn)

        self.setLayout(layout)
        self.setWindowTitle("USB Network & Video Stream")
        self.resize(640, 480)

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
        """Starts the GStreamer video feed inside the Qt GUI."""
        if self.pipeline:
            return  # Already running

        # Use appsink to capture frames instead of using a dedicated Qt sink
        self.pipeline = Gst.parse_launch(
            "udpsrc port=5000 ! application/x-rtp, encoding-name=JPEG, payload=26 ! "
            "rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink"
        )

        # Get the appsink element to extract frames
        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.set_property("emit-signals", True)
        self.appsink.set_property("max-buffers", 1)
        self.appsink.set_property("drop", True)
        self.appsink.connect("new-sample", self.on_new_sample)

        # Start pipeline
        self.pipeline.set_state(Gst.State.PLAYING)
        print("GStreamer started.")

    def stop_gstreamer(self):
        """Stops the GStreamer video stream."""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            print("GStreamer stopped.")

    def on_new_sample(self, sink):
        """Callback function to handle new frames from GStreamer."""
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            width = caps.get_structure(0).get_int("width")[1]
            height = caps.get_structure(0).get_int("height")[1]
            success, map_info = buf.map(Gst.MapFlags.READ)
            if success:
                try:
                    # Convert buffer to NumPy array
                    frame = np.frombuffer(map_info.data, dtype=np.uint8).reshape((height, width, 3))

                    # Convert frame to Qt image
                    qimg = QImage(frame.data, width, height, width * 3, QImage.Format.Format_BGR888)
                    pixmap = QPixmap.fromImage(qimg)
                    self.video_label.setPixmap(pixmap)
                finally:
                    buf.unmap(map_info)
            return Gst.FlowReturn.OK  # Fixes TypeError

    def closeEvent(self, event):
        """Ensure GStreamer stops when the app is closed."""
        self.stop_gstreamer()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoApp()
    window.show()
    sys.exit(app.exec())
