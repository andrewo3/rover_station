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