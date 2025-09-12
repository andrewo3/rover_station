from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

import numpy as np

# ---------------------------
# Navigation Tab Implementation
# ---------------------------
class NavTab(QWidget):
    def __init__(self):
        super().__init__()

        # Main layout
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # --------------------
        # LEFT SIDE
        # --------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Survey Base button
        survey_btn = QPushButton("Survey Base")
        survey_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        left_layout.addWidget(survey_btn, alignment=Qt.AlignLeft)

        # Coordinates label ABOVE the map
        coords_row = QHBoxLayout()
        coords_row.addStretch()
        self.coords_label = QLabel("Rover: (0,0)\nBase: (0,0)")
        coords_row.addWidget(self.coords_label, alignment=Qt.AlignRight)
        left_layout.addLayout(coords_row, stretch=0)  # minimal height

        # Map placeholder (expands to fill space)
        self.map_widget = QLabel("Map with Rover + Base Dots")
        self.map_widget.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        self.map_widget.setMinimumSize(400, 300)
        self.map_widget.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.map_widget, stretch=1)  # dominant space

        # Distance + heading row UNDER the map
        metrics_row = QHBoxLayout()
        self.distance_label = QLabel("Distance: 0.0 m")
        self.heading_label = QLabel("Heading: 0°")
        metrics_row.addWidget(self.distance_label, alignment=Qt.AlignLeft)
        metrics_row.addStretch()
        metrics_row.addWidget(self.heading_label, alignment=Qt.AlignRight)
        left_layout.addLayout(metrics_row, stretch=0)  # minimal height

        splitter.addWidget(left_panel)
        # --------------------
        # RIGHT SIDE
        # --------------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Log viewer + source switch button
        log_row = QHBoxLayout()
        self.log_label = QLabel("Monitoring: Rover")
        switch_btn = QPushButton("Switch Source")
        switch_btn.clicked.connect(self.switch_source)
        log_row.addWidget(self.log_label, alignment=Qt.AlignLeft)
        log_row.addWidget(switch_btn, alignment=Qt.AlignRight)
        right_layout.addLayout(log_row)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlainText("Log messages will appear here...\n")
        right_layout.addWidget(self.log_output, stretch=2)

        # Satellite signal strength bar chart
        self.fig, self.ax = plt.subplots(figsize=(4, 2))
        self.canvas = FigureCanvas(self.fig)
        right_layout.addWidget(self.canvas, stretch=1)

        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

        # State
        self.monitoring_rover = True

        # Initial plot
        self.plot_satellite_signals()

        # Example: auto-refresh chart every 2 seconds (can remove if not needed)
        self.timer = QTimer()
        self.timer.timeout.connect(self.plot_satellite_signals)
        self.timer.start(2000)

    def switch_source(self):
        """Switch between Rover and Base monitoring"""
        self.monitoring_rover = not self.monitoring_rover
        src = "Rover" if self.monitoring_rover else "Base"
        self.log_label.setText(f"Monitoring: {src}")
        self.log_output.append(f"Switched to monitoring {src}")
        self.plot_satellite_signals()

    def plot_satellite_signals(self, strengths=None):
        """Draw (or refresh) satellite signal strengths"""
        self.ax.clear()
        sats = np.arange(1, 9)  # 8 satellites
        if strengths is None:
            strengths = np.random.randint(20, 80, size=len(sats))  # placeholder
        self.ax.bar(sats, strengths)
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("Satellite ID")
        self.ax.set_ylabel("Signal Strength")
        src = "Rover" if self.monitoring_rover else "Base"
        self.ax.set_title(f"Signal Strengths ({src})")
        self.canvas.draw()