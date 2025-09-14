import sys
import threading
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QSplitter, QLineEdit
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from pexpect import pxssh
import pyte
from pexpect.exceptions import TIMEOUT

def render_pyte_screen_as_html(screen):
    html_lines = []
    for y, row in screen.buffer.items():        # row = dict of column -> Char
        line_html = ""
        for x in range(screen.columns):
            char = row.get(x)
            if char is None:
                line_html += " "
            else:
                text = char.data
                style = []
                if char.fg:
                    color = "white" if char.fg == "default" else char.fg
                    style.append(f"color:{color}")
                if char.bg:
                    color = "black" if char.bg == "default" else char.bg
                    style.append(f"background-color:{color}")
                if char.bold:
                    style.append("font-weight:bold")
                if char.underscore:
                    style.append("text-decoration:underline")
                if style:
                    line_html += f"<span style='{';'.join(style)}'>{text}</span>"
                else:
                    line_html += text
        html_lines.append(line_html)

    return "<br>".join(html_lines)

# Worker: runs SSH in background and feeds output to pyte screen
class SSHWorker(QObject):
    output_ready = Signal(str)  # emits HTML or text for display

    def __init__(self, host, user, password="", keyfile=None, cols=80, rows=24):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        self.keyfile = keyfile
        self.session = None
        self.running = True
        
        self.cols = 80
        self.rows = 30
        self.screen = pyte.Screen(self.cols, self.rows)
        self.stream = pyte.ByteStream()
        self.stream.attach(self.screen)

    def start(self):
        def run():
            try:
                self.session = pxssh.pxssh()
                self.session.login(self.host, self.user, password=self.password, auto_prompt_reset=False)
                self.session.send("\r")
                self.output_ready.emit("[Connected to SSH]\n")

                while self.running:
                    try:
                        data = self.session.read_nonblocking(size=1024, timeout=0.01)
                        if data:
                            # Feed raw SSH data into pyte for terminal emulation
                            #print(type(decoded))
                            self.stream.feed(data)
                            # Render screen buffer into a single string
                            #print(type(self.screen.display))
                            screen_text = "\n".join(self.screen.display)
                            self.output_ready.emit(screen_text)
                    except pxssh.ExceptionPxssh:
                        break
                    except TIMEOUT:
                        continue
                    except Exception as e:
                        continue
            except Exception as e:
                self.output_ready.emit(f"[Error: {e}]\n")

        threading.Thread(target=run, daemon=True).start()

    def send_input(self, text):
        if self.session:
            self.session.send(text)

    def stop(self):
        self.running = False
        if self.session:
            self.session.logout()

# QTextEdit subclass for interactive shell input
class InteractiveShell(QTextEdit):
    def __init__(self, worker):
        super().__init__()
        self.worker = worker
        self.total_text = ""
        self.append("[Interactive SSH Shell]\n")
        self.setStyleSheet("""
            background-color: black;
            color: white;          /* default text color */
            font-family: "Courier New", "Consolas", "Monaco", monospace; /* optional: use monospace font */
            font-size: 12pt;        /* optional: adjust size */
        """)
        self.setLineWrapMode(QTextEdit.NoWrap)  # no automatic wrapping
        self.setFont(QFont("Courier New", 12))   # fixed-width font

    def setCursor(self):
        cursor = self.textCursor()
        
        screen = self.worker.screen
        row, col = screen.cursor.y, screen.cursor.x
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down,n=row)
        cursor.movePosition(QTextCursor.MoveOperation.NextCharacter,n=col)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def keyPressEvent(self, event):
        self.setCursor()
        key = event.key()
        text = event.text()
        mods = event.modifiers()

        # Detect "Ctrl" consistently across OSes
        if sys.platform == "darwin":
            ctrl_pressed = bool(mods & Qt.MetaModifier)
        else:
            ctrl_pressed = bool(mods & Qt.ControlModifier)

        # Special handling for control shortcuts
        if ctrl_pressed:
            if key == Qt.Key_C:
                self.worker.send_input("\x03")  # ^C
                return
            elif key == Qt.Key_D:
                self.worker.send_input("\x04")  # ^D
                return
            elif key == Qt.Key_Z:
                self.worker.send_input("\x1A")  # ^Z
                return
            elif key == Qt.Key_L:
                self.worker.send_input("\x0C")  # ^L
                return

        # Enter, Tab, Backspace, etc. → send raw codes
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.worker.send_input("\r")
        elif key == Qt.Key_Backspace:
            self.worker.send_input("\x7f")  # DEL
        elif key == Qt.Key_Tab:
            self.worker.send_input("\t")    # HT (0x09)
        elif text:
            # Send all other printable characters
            self.worker.send_input(text)
        else:
            # Handle arrows, Home, End, etc.
            if key == Qt.Key_Left:
                self.worker.send_input("\x1b[D")
            elif key == Qt.Key_Right:
                self.worker.send_input("\x1b[C")
            elif key == Qt.Key_Up:
                self.worker.send_input("\x1b[A")
            elif key == Qt.Key_Down:
                self.worker.send_input("\x1b[B")
            elif key == Qt.Key_Home:
                self.worker.send_input("\x1b[H")
            elif key == Qt.Key_End:
                self.worker.send_input("\x1b[F")
            else:
                super().keyPressEvent(event)
        
    def mousePressEvent(self, event):
        self.setCursor()
        super().mousePressEvent(event)


    def focusInEvent(self, event):
        self.setCursor()
        super().focusInEvent(event)


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
        #self.conv = Ansi2HTMLConverter(inline=True)
        self.worker = SSHWorker("rover-jetson.local", "rover", password="[REPLACE WITH PASSWORD]")
        self.shell = InteractiveShell(self.worker)
        splitter.addWidget(self.shell)
        
        self.worker.output_ready.connect(self.display_output)
        self.worker.start()

        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

        
    def display_output(self, screen_text):
        html = render_pyte_screen_as_html(self.worker.screen)
        self.shell.setHtml(html)
        self.shell.setCursor()


        
    def handle_command(self):
        """Triggered when user presses Enter in the left command box"""
        cmd = self.command_input.text().strip()
        if cmd:
            self.log_output.append(f"> {cmd}")
            # TODO: send cmd to backend and append result
            self.log_output.append(f"(mock response to '{cmd}')\n")
        self.command_input.clear()