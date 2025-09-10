import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

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

        self.setWindowTitle("C2 Station")
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
        tabs.addTab(PlaceholderTab("Camera"), "Camera")
        tabs.addTab(PlaceholderTab("GPS"), "GPS")
        tabs.addTab(PlaceholderTab("Health"), "Health")
        tabs.addTab(PlaceholderTab("Control"), "Control")
        
        tab_bar = tabs.tabBar()
        tab_bar.setExpanding(True)

        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
