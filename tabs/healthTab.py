from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QTimer
import datetime
import socket
import threading
from time import sleep

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
        self.connected = False
        self.connection_thread = threading.Thread(target=self.connect_socket,daemon=True)
        self.connection_thread.start()

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
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)  # every 2s
        
    def connect_socket(self):
        while True:
            if not self.connected:
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect(("10.242.187.175",3000))
                    splash_text = self.sock.recv(1024).decode()
                    print(splash_text)
                    self.connected = True
                except ConnectionRefusedError:
                    continue
            else:
                try:
                    self.sock.send(b"network status")
                    resp = self.sock.recv(1024).decode()
                    lines = resp.splitlines()
                    values = lines[2].split()
                    quality = int(values[2].strip("."))
                    signal = int(values[3].strip("."))
                    noise = int(values[4].strip("."))
                    SNR = signal - noise
                    self.signal_24g.setText(f"2.4G: {SNR} dB - Quality: {quality}%")
                    sleep(2)
                except Exception as e:
                    self.connected = False
                    print(e)
    def update(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{now}] Example rover status message")