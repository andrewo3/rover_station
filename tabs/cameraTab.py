from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GstVideo

import numpy as np

Gst.init(None)

#Video Widget
class VideoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.pixmap = None
        self.analog = False

        if self.analog:
            # --- Analog camera pipeline ---
            pipeline_desc = (
                "avfvideosrc device-index=0 ! "
                "videoconvert ! "
                "video/x-raw,format=RGB ! "
                "appsink name=sink emit-signals=True sync=false"
            )
        else:
            # --- Digital UDP H264 pipeline ---
            pipeline_desc = (
                "udpsrc port=5000 caps=\"application/x-rtp, media=video, encoding-name=H264, payload=96\" ! "
                "rtpjitterbuffer latency=0 ! "
                "rtph264depay ! "
                "avdec_h264 ! "
                "videoconvert ! "
                "video/x-raw,format=RGB ! "
                "appsink name=sink emit-signals=True sync=false"
            )

        self.pipeline = Gst.parse_launch(pipeline_desc)

        self.appsink = self.pipeline.get_by_name("sink")
        self.appsink.connect("new-sample", self.on_new_sample)

        self.pipeline.set_state(Gst.State.PLAYING)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        caps = sample.get_caps()

        structure = caps.get_structure(0)
        width = structure.get_value("width")
        height = structure.get_value("height")

        success, mapinfo = buf.map(Gst.MapFlags.READ)
        if not success:
            return Gst.FlowReturn.ERROR

        arr = np.frombuffer(mapinfo.data, dtype=np.uint8)
        arr = arr.reshape((height, width, 3))

        image = QImage(
            arr.data,
            width,
            height,
            3 * width,
            QImage.Format.Format_RGB888
        )

        self.pixmap = QPixmap.fromImage(image)
        self.update()

        buf.unmap(mapinfo)
        return Gst.FlowReturn.OK

    def paintEvent(self, event):
        if not self.pixmap:
            return

        painter = QPainter(self)
        painter.drawPixmap(
            0, 0, self.width(), self.height(), self.pixmap
        )

# ---------------------------
# Camera Tab Implementation
# ---------------------------
class CameraTab(QWidget):
    def __init__(self):
        super().__init__()

        # Main vertical layout
        main_layout = QVBoxLayout(self)

        # Button always visible at top-left
        self.toggle_button = QPushButton("Toggle Multicam View")
        self.toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.toggle_button.clicked.connect(self.toggle_view)

        # Stacked layout for single vs multicam
        self.stacked_layout = QStackedLayout()

        # --- Single Camera View ---
        single_view = QWidget()
        single_layout = QHBoxLayout(single_view)

        # Left side: feed + nav buttons
        feed_with_nav = QVBoxLayout()

        #Camera live feed
        self.live_feed = VideoWidget()
        feed_with_nav.addWidget(self.live_feed)

        # Navigation row (same width as feed)
        nav_row = QHBoxLayout()
        prev_btn = QPushButton("Prev Camera")
        next_btn = QPushButton("Next Camera")
        nav_row.addWidget(prev_btn, alignment=Qt.AlignLeft)
        nav_row.addWidget(next_btn, alignment=Qt.AlignRight)

        feed_with_nav.addLayout(nav_row)

        single_layout.addLayout(feed_with_nav, stretch=3)

        # Right side: camera buttons grid
        button_grid_widget = QWidget()
        button_grid = QGridLayout(button_grid_widget)
        for i in range(2):
            for j in range(3):
                btn = QPushButton(f"Cam {i*3 + j + 1}")
                button_grid.addWidget(btn, i, j)
        single_layout.addWidget(button_grid_widget, stretch=1)

        self.stacked_layout.addWidget(single_view)

        # --- Multicam View ---
        multicam_view = QWidget()
        multicam_layout = QVBoxLayout(multicam_view)

        self.multicam_feed = QLabel("Multicam Feed")
        self.multicam_feed.setStyleSheet("background-color: black; color: white; border: 1px solid gray;")
        self.multicam_feed.setAlignment(Qt.AlignCenter)
        self.multicam_feed.setMinimumSize(600, 400)
        multicam_layout.addWidget(self.multicam_feed)

        self.stacked_layout.addWidget(multicam_view)

        # Add toggle + stacked view into main layout
        main_layout.addWidget(self.toggle_button, alignment=Qt.AlignLeft)
        main_layout.addLayout(self.stacked_layout)

        # Start in single camera view
        self.stacked_layout.setCurrentIndex(0)

    def toggle_view(self):
        """Switch between single and multicam views"""
        current = self.stacked_layout.currentIndex()
        self.stacked_layout.setCurrentIndex(1 if current == 0 else 0)