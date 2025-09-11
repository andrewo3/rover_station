import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QDoubleValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
import datetime

# ---------------------------
# Control Tab Implementation
# ---------------------------
class ControlTab(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        # --- Top Buttons ---
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Rover")
        self.stop_btn = QPushButton("Stop Rover")
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # --- Controller placeholders ---
        controllers_layout = QHBoxLayout()
        self.controller1 = QGroupBox("Controller 1")
        self.controller2 = QGroupBox("Controller 2")
        # Simple placeholder content
        c1_layout = QVBoxLayout(self.controller1)
        c1_layout.addWidget(QLabel("Controller 1 Visual Placeholder"), alignment=Qt.AlignCenter)
        c2_layout = QVBoxLayout(self.controller2)
        c2_layout.addWidget(QLabel("Controller 2 Visual Placeholder"), alignment=Qt.AlignCenter)
        controllers_layout.addWidget(self.controller1, stretch=1)
        controllers_layout.addWidget(self.controller2, stretch=1)
        main_layout.addLayout(controllers_layout)

        # --- Bottom Row: Arm Control & Drive Control ---
        bottom_layout = QHBoxLayout()

        # Arm Control Panel
        self.arm_panel = self.create_arm_panel()
        bottom_layout.addWidget(self.arm_panel, stretch=1)

        # Drive Control Panel
        self.drive_panel = self.create_drive_panel()
        bottom_layout.addWidget(self.drive_panel, stretch=1)

        main_layout.addLayout(bottom_layout)

    def create_arm_panel(self):
        panel = QGroupBox("Arm Control (Individual Motor + End Effector IK Control)")
        layout = QVBoxLayout(panel)

        # Switch for End Effector Control
        self.ee_switch = QCheckBox("End Effector Control")
        self.ee_switch.stateChanged.connect(self.toggle_arm_labels)
        layout.addWidget(self.ee_switch)

        # Arm labels (joint mode) and EE labels
        self.joint_labels = ["Azimuth", "Shoulder", "Elbow", "Wrist1", "Wrist2", "Wrist3", "Gripper"]
        self.ee_labels    = ["x", "y", "z", "Rx", "Ry", "Rz", "Gripper"]

        # Storage for values for each mode (strings). Start with zeros.
        self.joint_values = ["0.0"] * len(self.joint_labels)
        self.ee_values = ["0.0"] * len(self.ee_labels)

        # Create fields
        self.arm_fields = []  # list of tuples (label_widget, edit_widget)
        validator = QDoubleValidator(bottom=-1e6, top=1e6, decimals=6)
        grid = QGridLayout()
        for i, label in enumerate(self.joint_labels):
            lbl = QLabel(label)
            edit = QLineEdit()
            edit.setValidator(validator)
            edit.setText(self.joint_values[i])
            # Wrist3 is greyed out in joint mode initially
            if label == "Wrist3":
                edit.setEnabled(False)
            grid.addWidget(lbl, i, 0)
            grid.addWidget(edit, i, 1)
            self.arm_fields.append((lbl, edit))
        layout.addLayout(grid)

        # Get / Send buttons
        btn_layout = QHBoxLayout()
        self.get_btn = QPushButton("Get")
        self.send_btn = QPushButton("Send")
        self.get_btn.clicked.connect(self.on_get_arm)
        self.send_btn.clicked.connect(self.on_send_arm)
        btn_layout.addWidget(self.get_btn)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return panel

    def toggle_arm_labels(self):
        """Swap labels between joint and EE mode, save & restore values, enable/disable Wrist3."""
        # Determine which storage to save to and which to load from
        if self.ee_switch.isChecked():
            # switching into EE mode: save current joint values, load ee values
            self._save_current_arm_values(to_joint=True)
            self._load_arm_values(from_joint=False)
            # enable Wrist3 in EE mode
            _, wrist3_edit = self.arm_fields[5]
            wrist3_edit.setEnabled(True)
        else:
            # switching into Joint mode: save current ee values, load joint values
            self._save_current_arm_values(to_joint=False)
            self._load_arm_values(from_joint=True)
            # disable Wrist3 in joint mode
            _, wrist3_edit = self.arm_fields[5]
            wrist3_edit.setEnabled(False)

    def _save_current_arm_values(self, to_joint: bool):
        """Save the current edits into the appropriate storage.
        If to_joint is True, we save UI values into joint_values (we are leaving joint mode),
        otherwise we save UI values into ee_values."""
        values = []
        for _, edit in self.arm_fields:
            text = edit.text().strip()
            # Keep it as string even if empty so it can be reinstated
            values.append(text if text != "" else "0.0")
        if to_joint:
            self.joint_values = values
        else:
            self.ee_values = values

    def _load_arm_values(self, from_joint: bool):
        """Load values into the UI. If from_joint True, load joint_values; otherwise load ee_values.
           Also update labels to the corresponding names."""
        if from_joint:
            labels = self.joint_labels
            values = self.joint_values
        else:
            labels = self.ee_labels
            values = self.ee_values

        for (lbl_widget, edit_widget), new_label, val in zip(self.arm_fields, labels, values):
            lbl_widget.setText(new_label)
            # set validator-safe text
            edit_widget.setText(val if val is not None else "0.0")

    def on_get_arm(self):
        # Example: pretend to query hardware and update fields for current mode.
        # We'll just set some dummy values for demonstration.
        if self.ee_switch.isChecked():
            # EE mode
            sample = ["1.23", "4.56", "7.89", "0.1", "0.2", "0.3", "0.0"]
            self.ee_values = sample
            self._load_arm_values(from_joint=False)
        else:
            # Joint mode
            sample = ["10.0", "20.0", "30.0", "5.0", "6.0", "7.0", "0.0"]
            self.joint_values = sample
            self._load_arm_values(from_joint=True)

    def on_send_arm(self):
        # Gather the current UI values and "send" them (placeholder)
        current_values = [edit.text().strip() for _, edit in self.arm_fields]
        if self.ee_switch.isChecked():
            mode = "EE"
            self.ee_values = [v if v != "" else "0.0" for v in current_values]
        else:
            mode = "Joint"
            self.joint_values = [v if v != "" else "0.0" for v in current_values]
        print(f"[Send Arm] Mode={mode}, values={current_values}")
        # TODO: send to backend

    def create_drive_panel(self):
        panel = QGroupBox("Drive Control (Individual Motor / Velocity Control)")
        layout = QVBoxLayout(panel)

        grid = QGridLayout()
        self.rpm_labels = []
        self.target_fields = []

        validator = QDoubleValidator(bottom=-1e6, top=1e6, decimals=3)

        for i in range(6):
            rpm_lbl = QLabel(f"Motor {i+1}: 0 RPM")
            rpm_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            tgt_edit = QLineEdit()
            tgt_edit.setValidator(validator)
            tgt_edit.setPlaceholderText("target RPM")
            grid.addWidget(rpm_lbl, i, 0)
            grid.addWidget(tgt_edit, i, 1)
            self.rpm_labels.append(rpm_lbl)
            self.target_fields.append(tgt_edit)

        layout.addLayout(grid)

        # Play / Stop buttons with standard icons
        btn_layout = QHBoxLayout()
        play_icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        stop_icon = self.style().standardIcon(QStyle.SP_MediaStop)
        self.play_btn = QPushButton()
        self.play_btn.setIcon(play_icon)
        self.play_btn.clicked.connect(self.on_drive_play)
        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(stop_icon)
        self.stop_btn.clicked.connect(self.on_drive_stop)
        btn_layout.addStretch()
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        return panel

    def on_drive_play(self):
        # Collect targets and "start" drive control
        targets = [edit.text().strip() for edit in self.target_fields]
        print("[Drive] Play - targets:", targets)
        # TODO: send to backend

    def on_drive_stop(self):
        print("[Drive] Stop")
        # TODO: send stop command to backend

# ---------------------------
# Health Tab Implementation
# ---------------------------
class HealthTab(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        # ---- Grid of telemetry values ----
        grid = QGridLayout()

        # Battery (left)
        grid.addWidget(QLabel("<b>Battery</b>"), 0, 0, alignment=Qt.AlignCenter)
        self.batt_voltage = QLabel("xx.x V")
        self.batt_percent = QLabel("xx.x%")
        grid.addWidget(self.batt_voltage, 1, 0, alignment=Qt.AlignCenter)
        grid.addWidget(self.batt_percent, 2, 0, alignment=Qt.AlignCenter)

        # Power Draw (left, below Battery)
        grid.addWidget(QLabel("<b>Power Draw</b>"), 3, 0, alignment=Qt.AlignCenter)
        self.power_current = QLabel("xx.x A")
        self.power_watts = QLabel("xx.x W")
        grid.addWidget(self.power_current, 4, 0, alignment=Qt.AlignCenter)
        grid.addWidget(self.power_watts, 5, 0, alignment=Qt.AlignCenter)

        # VREFs (middle, stacked vertically)
        grid.addWidget(QLabel("<b>18VREF</b>"), 0, 1, alignment=Qt.AlignCenter)
        self.vref18 = QLabel("xx.x V")
        grid.addWidget(self.vref18, 1, 1, alignment=Qt.AlignCenter)

        grid.addWidget(QLabel("<b>12VREF</b>"), 2, 1, alignment=Qt.AlignCenter)
        self.vref12 = QLabel("xx.x V")
        grid.addWidget(self.vref12, 3, 1, alignment=Qt.AlignCenter)

        grid.addWidget(QLabel("<b>5VREF</b>"), 4, 1, alignment=Qt.AlignCenter)
        self.vref5 = QLabel("xx.x V")
        grid.addWidget(self.vref5, 5, 1, alignment=Qt.AlignCenter)

        # Signal (top right)
        grid.addWidget(QLabel("<b>Signal</b>"), 0, 2, alignment=Qt.AlignCenter)
        self.signal_24g = QLabel("2.4G: xx.x dBm")
        self.signal_900m = QLabel("900M: xx.x dBm")
        grid.addWidget(self.signal_24g, 1, 2, alignment=Qt.AlignCenter)
        grid.addWidget(self.signal_900m, 2, 2, alignment=Qt.AlignCenter)

        # Drive (right side, stacked)
        grid.addWidget(QLabel("<b>Drive</b>"), 3, 2, alignment=Qt.AlignCenter)
        self.drive_currents = []
        for i in range(6):
            lbl = QLabel(f"Motor {i+1}: xx.x A")
            grid.addWidget(lbl, 4 + i, 2, alignment=Qt.AlignCenter)
            self.drive_currents.append(lbl)

        # Estimated Remaining Operation Time (bottom, centered)
        grid.addWidget(QLabel("<b>Estimated Remaining Operation Time</b>"), 10, 1, alignment=Qt.AlignCenter)
        self.remaining_time = QLabel("hh:mm:ss")
        grid.addWidget(self.remaining_time, 11, 1, alignment=Qt.AlignCenter)

        main_layout.addLayout(grid)

        # ---- Log output ----
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: black; color: lime;")
        main_layout.addWidget(self.log_output, stretch=1)

        # ---- Example log updater ----
        self.timer = QTimer()
        self.timer.timeout.connect(self.append_log)
        self.timer.start(2000)  # every 2s

    def append_log(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{now}] Example rover status message")

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
        tabs.addTab(GPSTab(), "Navigation")
        tabs.addTab(HealthTab(), "Health")
        tabs.addTab(ControlTab(), "Control")
        tabs.addTab(PlaceholderTab("Science"), "Science")
        
        tab_bar = tabs.tabBar()
        tab_bar.setExpanding(True)

        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
