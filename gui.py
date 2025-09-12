import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from tabs.shellTab import ShellTab
from tabs.cameraTab import CameraTab
from tabs.navTab import NavTab
from tabs.healthTab import HealthTab
from tabs.controlTab import ControlTab

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
        tabs.addTab(NavTab(), "Navigation")
        tabs.addTab(HealthTab(), "Health")
        tabs.addTab(ControlTab(), "Control")
        tabs.addTab(PlaceholderTab("Science"), "Science")
        
        tab_bar = tabs.tabBar()
        tab_bar.setExpanding(True)

        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
