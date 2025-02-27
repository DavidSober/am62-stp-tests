import sys
import subprocess
import gi
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication


def enable_dark_mode(app):
    """Applies a dark theme to the PyQt5 app."""
    app.setStyle("Fusion")

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)


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
        self.pipeline1 = None
        self.pipeline2 = None
        self.appsink1 = None
        self.appsink2 = None

    def initUI(self):
        layout = QVBoxLayout()

        # Network "Connect" button
        self.connect_btn = QPushButton("Connect", self)
        self.connect_btn.clicked.connect(self.setup_usb_network)
        layout.addWidget(self.connect_btn)

        # **Dual Video Layout**
        video_layout = QHBoxLayout()
        
        # First Camera Video Label
        self.video_label1 = QLabel(self)
        self.video_label1.setText("Camera 1")
        video_layout.addWidget(self.video_label1)

        # Second Camera Video Label
        self.video_label2 = QLabel(self)
        self.video_label2.setText("Camera 2")
        video_layout.addWidget(self.video_label2)

        layout.addLayout(video_layout)

        # Start/Stop buttons for both feeds
        self.start_video_btn = QPushButton("Start Both Videos", self)
        self.start_video_btn.clicked.connect(self.start_gstreamer)
        layout.addWidget(self.start_video_btn)

        self.stop_video_btn = QPushButton("Stop Both Videos", self)
        self.stop_video_btn.clicked.connect(self.stop_gstreamer)
        layout.addWidget(self.stop_video_btn)

        self.setLayout(layout)
        self.setWindowTitle("USB Network & Dual Video Stream")
        self.resize(1280, 480)  # Wider window for two video feeds

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
        """Starts both GStreamer video feeds inside the Qt GUI."""
        if self.pipeline1 or self.pipeline2:
            return  # Already running

        # **Pipeline for Camera 1 (port=5000)**
        self.pipeline1 = Gst.parse_launch(
            "udpsrc port=5000 ! application/x-rtp, encoding-name=JPEG, payload=26 ! "
            "rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink1"
        )
        self.appsink1 = self.pipeline1.get_by_name("sink1")
        self.appsink1.set_property("emit-signals", True)
        self.appsink1.set_property("max-buffers", 1)
        self.appsink1.set_property("drop", True)
        self.appsink1.connect("new-sample", self.on_new_sample1)

        # **Pipeline for Camera 2 (port=5001)**
        self.pipeline2 = Gst.parse_launch(
            "udpsrc port=5001 ! application/x-rtp, encoding-name=JPEG, payload=26 ! "
            "rtpjpegdepay ! jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink name=sink2"
        )
        self.appsink2 = self.pipeline2.get_by_name("sink2")
        self.appsink2.set_property("emit-signals", True)
        self.appsink2.set_property("max-buffers", 1)
        self.appsink2.set_property("drop", True)
        self.appsink2.connect("new-sample", self.on_new_sample2)

        # Start both pipelines
        self.pipeline1.set_state(Gst.State.PLAYING)
        self.pipeline2.set_state(Gst.State.PLAYING)
        print("GStreamer started for both cameras.")

    def stop_gstreamer(self):
        """Stops both GStreamer video streams."""
        if self.pipeline1:
            self.pipeline1.set_state(Gst.State.NULL)
            self.pipeline1 = None
        if self.pipeline2:
            self.pipeline2.set_state(Gst.State.NULL)
            self.pipeline2 = None
        print("GStreamer stopped for both cameras.")

    def on_new_sample1(self, sink):
        """Handles new frames for Camera 1."""
        return self.process_frame(sink, self.video_label1)

    def on_new_sample2(self, sink):
        """Handles new frames for Camera 2."""
        return self.process_frame(sink, self.video_label2)

    def process_frame(self, sink, label):
        """Processes new video frames and updates the correct QLabel."""
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            width = caps.get_structure(0).get_int("width")[1]
            height = caps.get_structure(0).get_int("height")[1]
            success, map_info = buf.map(Gst.MapFlags.READ)
            if success:
                try:
                    frame = np.frombuffer(map_info.data, dtype=np.uint8).reshape((height, width, 3))
                    qimg = QImage(frame.data, width, height, width * 3, QImage.Format.Format_BGR888)
                    pixmap = QPixmap.fromImage(qimg)
                    label.setPixmap(pixmap)
                finally:
                    buf.unmap(map_info)
            return Gst.FlowReturn.OK

    def closeEvent(self, event):
        """Ensure GStreamer stops when the app is closed."""
        self.stop_gstreamer()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply dark mode
    enable_dark_mode(app)
    window = VideoApp()
    window.show()
    sys.exit(app.exec())
