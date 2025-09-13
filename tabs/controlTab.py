from PySide6.QtWidgets import *

from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRectF
from PySide6.QtGui import QDoubleValidator, QTransform, QPainter
import numpy as np
import controller
import os

next_scan = 0
num_controllers = 2

class CroppedSvgItem(QGraphicsSvgItem):
    def __init__(self, filename):
        super().__init__(filename)
        self._crop = None  # QRectF in item-local coordinates

    def setCropRect(self, rect: QRectF | None):
        """rect is in the item's local coordinates (before item's transform)."""
        self._crop = QRectF(rect) if rect is not None else None
        self.update()  # request repaint

    def paint(self, painter: QPainter, option, widget):
        if self._crop:
            painter.save()
            # clip in the item-local coordinate system (this is the painter's
            # coordinate system inside paint())
            painter.setClipRect(self._crop)
            super().paint(painter, option, widget)
            painter.restore()
        else:
            super().paint(painter, option, widget)

class ControllerScanner(QThread):
    found = Signal(list)  # Emits list of available controllers

    def run(self):
        avail = controller.find_controllers()
        self.found.emit(avail)

class XboxControllerWidget(QWidget):
    def __init__(self, asset_folder, index):
        super().__init__()

        self.scanner = None
        self.asset_folder = asset_folder

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        
        self.joy_dist = 25
        self.cont = None
        # Base controller SVG
        self.disconnected = QGraphicsSvgItem(os.path.join(asset_folder, "disconnected.svg"))
        #self.disconnected.setFixedSize(400, 300)
        self.base = QGraphicsSvgItem(os.path.join(asset_folder, "base-black.svg"))
        self.scene.addItem(self.base)
        self.scene.addItem(self.disconnected)
        #self.base_controller.setFixedSize(400, 300)
        self.abxy = QSvgRenderer(os.path.join(asset_folder, "buttons.svg"))
        self.lbumper = QGraphicsSvgItem(os.path.join(asset_folder, "bumper.svg"))
        self.rbumper = QGraphicsSvgItem(os.path.join(asset_folder, "bumper.svg"))
        self.rbumper.setTransform(QTransform().scale(-1,1))

        self.dpad = QSvgRenderer(os.path.join(asset_folder, "dpad.svg"))

        self.startback = QSvgRenderer(os.path.join(asset_folder, "start-select.svg"))

        self.stick = QSvgRenderer(os.path.join(asset_folder, "stick.svg"))
        self.ltrigger = CroppedSvgItem(os.path.join(asset_folder, "trigger.svg"))
        self.rtrigger = CroppedSvgItem(os.path.join(asset_folder, "trigger.svg"))
        self.rtrigger.setTransform(QTransform().scale(-1,1))

        self.scene.addItem(self.lbumper)
        self.scene.addItem(self.rbumper)

        self.lbumper.setPos(107,130)
        self.rbumper.setPos(645,130)

        self.lbumper.setVisible(False)
        self.rbumper.setVisible(False)

        self.scene.addItem(self.ltrigger)
        self.scene.addItem(self.rtrigger)

        self.ltrigger.setPos(152,0)
        self.rtrigger.setPos(598,0)

        self.ltrigger.setVisible(True)
        self.rtrigger.setVisible(True)
        
        self.button_svgs = {}

        for button in ["A","B","X","Y"]:
            self.button_svgs[button] = []
            for state in ["Unpressed","Pressed"]:
                item = QGraphicsSvgItem()
                item.setSharedRenderer(self.abxy)
                item.setElementId(button + "-"+ state)
                item.setVisible(False)
                self.scene.addItem(item)
                self.button_svgs[button].append(item)
                if button == "A":
                    item.setPos(540,300)
                elif button == "Y":
                    item.setPos(540,200)
                elif button == "X":
                    item.setPos(490,250)
                elif button == "B":
                    item.setPos(590,250)
        
        for pad in ["up","down","left","right"]:
            item = QGraphicsSvgItem()
            item.setSharedRenderer(self.dpad)
            item.setElementId("dpad-"+ pad)
            item.setVisible(False)
            self.scene.addItem(item)
            if pad == "up":
                item.setPos(260,345)
            elif pad == "down":
                item.setPos(260,400)
            elif pad == "left":
                item.setPos(222,385)
            elif pad == "right":
                item.setPos(275,385)
            self.button_svgs[pad] = item

        for button in ["start","back"]:
            item = QGraphicsSvgItem()
            item.setSharedRenderer(self.startback)
            item.setElementId(button)
            item.setVisible(False)
            self.scene.addItem(item)
            if button == "start":
                item.setPos(413,263)
            elif button == "back":
                item.setPos(305,263)
            self.button_svgs[button] = item

        for joy in ["Left","Right"]:
            self.button_svgs[joy[0]+"S"] = []
            for state in ["Unpressed","Pressed"]:
                item = QGraphicsSvgItem()
                item.setSharedRenderer(self.stick)
                item.setElementId("Joy-"+ state)
                item.setVisible(True)
                if joy == "Left":
                    item.setPos(145,240)
                elif joy == "Right":
                    item.setPos(431,352)
                self.scene.addItem(item)
                self.button_svgs[joy[0]+"S"].append(item)


        self.button_svgs["LT"] = self.ltrigger
        self.button_svgs["RT"] = self.rtrigger

        self.button_svgs["LB"] = self.lbumper
        self.button_svgs["RB"] = self.rbumper

        self.amax = np.pi/6

        self.disconnected.setZValue(10)
        self.disconnected.setVisible(True)

        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.check_controllers)
        self.scan_timer.start(500)

        self.cont_timer = QTimer()
        self.cont_timer.timeout.connect(self.run_controllers)
        self.cont_timer.start(30)
        
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.setMinimumSize(300, 250)
        layout.addWidget(self.view)
        
        self.view.setStyleSheet("background: transparent; border: none;")
        
        self.index = index
        
    
    def joyMat(self,x,y):
        r = 1/np.sin(self.amax)
        d = np.hypot(x,-y)
        if d != 0:
            sx = np.sqrt(1-(d/r)**2)
            sy = 1
            sAng = -y/d
            cAng = x/d 
            M = QTransform(
                cAng, sAng,
                -sAng, cAng,
                0, 0
            )
            N = QTransform(
                sx*cAng, -sx*sAng,
                sy*sAng, sy*cAng,
                0, 0
            )
            M*=N
        else:
            M = QTransform(
                1, 0,
                0, 1,
                0, 0
            )
        return M


    def run_controllers(self):
        if self.cont:
            self.button_svgs["A"][self.cont.button_data.a].setVisible(True)
            self.button_svgs["A"][not self.cont.button_data.a].setVisible(False)

            self.button_svgs["B"][self.cont.button_data.b].setVisible(True)
            self.button_svgs["B"][not self.cont.button_data.b].setVisible(False)

            self.button_svgs["X"][self.cont.button_data.x].setVisible(True)
            self.button_svgs["X"][not self.cont.button_data.x].setVisible(False)

            self.button_svgs["Y"][self.cont.button_data.y].setVisible(True)
            self.button_svgs["Y"][not self.cont.button_data.y].setVisible(False)

            self.button_svgs["LB"].setVisible(self.cont.button_data.bumper_left)
            self.button_svgs["RB"].setVisible(self.cont.button_data.bumper_right)

            self.button_svgs["up"].setVisible(self.cont.button_data.dpad_up)
            self.button_svgs["down"].setVisible(self.cont.button_data.dpad_down)
            self.button_svgs["left"].setVisible(self.cont.button_data.dpad_left)
            self.button_svgs["right"].setVisible(self.cont.button_data.dpad_right)

            self.button_svgs["start"].setVisible(self.cont.button_data.start)
            self.button_svgs["back"].setVisible(self.cont.button_data.back)

            self.button_svgs["LS"][self.cont.button_data.stick_left_click].setVisible(True)
            lx,ly = self.cont.button_data.stick_left_x/(1<<15),-self.cont.button_data.stick_left_y/(1<<15)
            self.button_svgs["LS"][self.cont.button_data.stick_left_click].setPos(145+lx*self.joy_dist,240+ly*self.joy_dist)
            center_x = self.button_svgs["LS"][self.cont.button_data.stick_left_click].boundingRect().width() / 2
            center_y = self.button_svgs["LS"][self.cont.button_data.stick_left_click].boundingRect().height() / 2
            T = QTransform()
            T.translate(-center_x,-center_y)
            T *= self.joyMat(lx,ly)
            T.translate(center_x,center_y)
            self.button_svgs["LS"][self.cont.button_data.stick_left_click].setTransform(T)
            self.button_svgs["LS"][not self.cont.button_data.stick_left_click].setVisible(False)

            self.button_svgs["RS"][self.cont.button_data.stick_right_click].setVisible(True)
            rx,ry = self.cont.button_data.stick_right_x/(1<<15),-self.cont.button_data.stick_right_y/(1<<15)
            self.button_svgs["RS"][self.cont.button_data.stick_right_click].setPos(431+rx*self.joy_dist,352+ry*self.joy_dist)
            center_x = self.button_svgs["RS"][self.cont.button_data.stick_right_click].boundingRect().width() / 2
            center_y = self.button_svgs["RS"][self.cont.button_data.stick_right_click].boundingRect().height() / 2
            T = QTransform()
            T.translate(-center_x,-center_y)
            T *= self.joyMat(rx,ry)
            T.translate(center_x,center_y)
            self.button_svgs["RS"][self.cont.button_data.stick_right_click].setTransform(T)
            self.button_svgs["RS"][not self.cont.button_data.stick_right_click].setVisible(False)

            tw = 88.934
            th = 121.795
            lamt = float(self.cont.button_data.trigger_left/(1<<10))
            self.button_svgs["LT"].setCropRect(QRectF(0,th-th*lamt,tw,th*lamt))

            ramt = float(self.cont.button_data.trigger_right/(1<<10))
            self.button_svgs["RT"].setCropRect(QRectF(0,th-th*ramt,tw,th*ramt))

    def scan_controllers(self):
        global next_scan
        if next_scan != self.index:
            return
        next_scan = -1
        self.scanner = ControllerScanner()
        self.scanner.found.connect(self.update_controller)
        self.scanner.finished.connect(self.scan_finished)
        self.scanner.start() 

    def scan_finished(self):
        global next_scan, num_controllers
        self.scanner = None
        next_scan = (self.index + 1) % num_controllers

    def check_controllers(self):
        if self.cont is None or (self.cont.started and not self.cont.connected):
            # Start a background scan
            self.scan_controllers()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Scale scene to fit the view every time
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
        
    def showEvent(self, event):
        super().showEvent(event)
        # ensure fitInView is applied once the widget is actually shown
        QTimer.singleShot(0, lambda: self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio))
        
    def update_controller(self, avail):
        """
        Scan for controllers and update button overlays when buttons are pressed.
        """
        try:
            self.cont = controller.PowerAController(avail[self.index])
            self.disconnected.setVisible(False)
        except IndexError as e:
            self.disconnected.setVisible(True)
                
                
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
        c1_layout.addWidget(XboxControllerWidget("xbox-one",0), alignment=Qt.AlignCenter)
        c2_layout = QVBoxLayout(self.controller2)
        c2_layout.addWidget(XboxControllerWidget("xbox-one",1), alignment=Qt.AlignCenter)
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
        for _, edit in self.arm_fields[:-1]:
            text = edit.text().strip()
            # Keep it as string even if empty so it can be reinstated
            values.append(text if text != "" else "0.0")
        if to_joint:
            self.joint_values[:-1] = values
        else:
            self.ee_values[:-1] = values

    def _load_arm_values(self, from_joint: bool):
        """Load values into the UI. If from_joint True, load joint_values; otherwise load ee_values.
           Also update labels to the corresponding names."""
        if from_joint:
            labels = self.joint_labels
            values = self.joint_values[:-1]
        else:
            labels = self.ee_labels
            values = self.ee_values[:-1]

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