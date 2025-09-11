import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------
# GPS Tab Implementation
# ---------------------------
class GPSTab(QWidget):
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

        # Live feed placeholder
        self.live_feed = QLabel("Live Camera Feed")
        self.live_feed.setStyleSheet("background-color: black; color: white; border: 1px solid gray;")
        self.live_feed.setAlignment(Qt.AlignCenter)
        self.live_feed.setMinimumSize(400, 300)
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

# ---------------------------
# Shell Tab Implementation
# ---------------------------
class ShellTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # -------------------
        # Left panel (log + input)
        # -------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Log output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: black; color: white; font-family: monospace;")
        self.log_output.setPlainText("System Log:\n> Ready...\n")
        left_layout.addWidget(self.log_output, stretch=4)

        # Command input
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("background-color: #111; color: white; font-family: monospace;")
        self.command_input.setPlaceholderText("Enter command...")
        self.command_input.returnPressed.connect(self.handle_command)
        left_layout.addWidget(self.command_input, stretch=0)

        splitter.addWidget(left_panel)

        # -------------------
        # Right panel (interactive shell area)
        # -------------------
        self.interactive_shell = QTextEdit()
        self.interactive_shell.setStyleSheet("background-color: black; color: white; font-family: monospace;")
        self.interactive_shell.setPlainText("SSH Session:\n$ ")
        # NOTE: not read-only → user can type directly here
        splitter.addWidget(self.interactive_shell)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

    def handle_command(self):
        """Triggered when user presses Enter in the left command box"""
        cmd = self.command_input.text().strip()
        if cmd:
            self.log_output.append(f"> {cmd}")
            # TODO: send cmd to backend and append result
            self.log_output.append(f"(mock response to '{cmd}')\n")
        self.command_input.clear()


# ---------------------------
# Placeholder Tab
# ---------------------------
class PlaceholderTab(QWidget):
    def __init__(self, name: str):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{name} Page Content"))

# ---------------------------
# Main Window
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("HURC Base Station")
        self.setGeometry(200, 200, 800, 400)

        # Create the tab widget
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)  # Tabs on top
        tabs.setTabShape(QTabWidget.Rounded)
        tabs.setMovable(False)
        tabs.setDocumentMode(True)
        tabs.setElideMode(Qt.ElideNone)
        tabs.setUsesScrollButtons(False)  # Tabs will expand instead of scrolling
        

        # Make tabs expand equally across the whole width
        tabs.addTab(ShellTab(), "Shell")
        tabs.addTab(CameraTab(), "Camera")
        tabs.addTab(GPSTab(), "GPS")
        tabs.addTab(PlaceholderTab("Health"), "Health")
        tabs.addTab(PlaceholderTab("Control"), "Control")
        tabs.addTab(PlaceholderTab("Science"), "Science")
        
        tab_bar = tabs.tabBar()
        tab_bar.setExpanding(True)

        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
