import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QStackedWidget, QHBoxLayout, QFileDialog, QSlider, QLineEdit, QFrame
from PyQt5.QtCore import Qt
import PyQt5.QtGui as QtGui
import serial.tools.list_ports
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox
from views.newMapping import NewMapping
from widgets.titleWidget import TitleWidget
from views.uploadWindow import UploadWindow
from views.noWindow import NoWindow
from views.minimapWindow import MinimapWindow
from views.consoleWindow import Console
from views.DeadReckoningPage import DeadReckoningPage
from views.RadarPage import RadarPage
from views.IMURADARTEST import QuickTest
import globalVariables

TILE_SIZE = 1  # Size of each tile
PLAYER_SIZE = 10  # Size of red dot
TRAIL_SIZE = 10  # Number of steps to keep the trail

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Log: Initialising MainWindow")
        self.setWindowTitle("Firefighter Tracker")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))

        self.mainPage = self.initWindow()

        self.uploadPage = UploadWindow(self.stack)  # Pass the stack reference
        #self.noPage = NoWindow("Firefighter Tracker - No Page", self.stack)  # Pass the stack reference
        self.consolePage = Console("Console Page", self.stack)  # Pass the stack reference

        self.noPage = NewMapping(self.stack)  # Pass the stack reference

        self.dead_reckoning_page = DeadReckoningPage(self.stack, "IMU Visualisation")  # Pass the stack reference
        self.radar_page = RadarPage(self.stack)
        self.test_page = QuickTest(self.stack)
        
        self.stack.addWidget(self.mainPage)
        self.stack.addWidget(self.uploadPage)
        self.stack.addWidget(self.noPage)
        self.stack.addWidget(self.consolePage)
        self.stack.addWidget(self.dead_reckoning_page)
        self.stack.addWidget(self.radar_page)
        self.stack.addWidget(self.test_page)
        self.apply_stylesheet("assets/stylesheets/base.qss")
        self.showMaximized()
        print("Log: MainWindow initialised and maximised")

    def initWindow(self):
        print("Log: Initialising main window layout")
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        titleCard = TitleWidget("Firefighter Tracker", "Do you have a floorplan?", "assets/images/SFRS Logo.png")

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_yes = QPushButton("Yes")
        btn_yes.setObjectName("btnYes")
        btn_yes.clicked.connect(self.on_yes_button_clicked)
        print("Log: 'Yes' button created")

        btn_no = QPushButton("No")
        btn_no.setObjectName("btnNo")
        btn_no.clicked.connect(self.on_no_button_clicked)
        print("Log: 'No' button created")

        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)

        btn_scan_com = QPushButton("Scan USB Port For Device")
        btn_scan_com.setObjectName("btnYes")
        btn_scan_com.setFixedWidth(348)
        btn_scan_com.setFixedHeight(40)
        btn_scan_com.clicked.connect(self.scan_com_port)
        print("Log: 'Scan USB Port For Device' button created")

        self.com_port_dropdown = QComboBox()
        self.com_port_dropdown.setObjectName("comPortDropdown")
        self.com_port_dropdown.setEditable(False)
        self.com_port_dropdown.activated.connect(self.update_selected_com_port)
        self.com_port_dropdown.setFixedWidth(348)
        self.com_port_dropdown.setFixedHeight(40)
        print("Log: COM port dropdown created")

        btn_console = QPushButton("Console Page")
        btn_console.setObjectName("btnYes")
        btn_console.setFixedWidth(348)
        btn_console.setFixedHeight(40)
        btn_console.clicked.connect(self.on_console_button_clicked)
        print("Log: 'Scan USB Port For Device' button created")

        btn_IMU = QPushButton("IMU Demo Page")
        btn_IMU.setObjectName("btnYes")
        btn_IMU.setFixedWidth(348)
        btn_IMU.setFixedHeight(40)
        btn_IMU.clicked.connect(self.on_IMU_button_clicked)
        print("Log: 'Scan USB Port For Device' button created")

        btn_RADAR = QPushButton("Radar Demo Page")
        btn_RADAR.setObjectName("btnYes")
        btn_RADAR.setFixedWidth(348)
        btn_RADAR.setFixedHeight(40)
        btn_RADAR.clicked.connect(self.on_radar_button_clicked)
        print("Log: 'Scan USB Port For Device' button created")

        
        btn_RADARTEST = QPushButton("Radar & IMU Demo Page")
        btn_RADARTEST.setObjectName("btnYes")
        btn_RADARTEST.setFixedWidth(348)
        btn_RADARTEST.setFixedHeight(40)
        btn_RADARTEST.clicked.connect(self.on_test_button_clicked)
        print("Log: 'Scan USB Port For Device' button created")

        layout.addWidget(titleCard)
        layout.addLayout(btn_layout)
        layout.addWidget(btn_scan_com, alignment=Qt.AlignCenter)
        layout.addWidget(self.com_port_dropdown, alignment=Qt.AlignCenter)
        layout.addWidget(btn_console, alignment=Qt.AlignCenter)
        layout.addWidget(btn_IMU, alignment=Qt.AlignCenter)
        layout.addWidget(btn_RADAR, alignment=Qt.AlignCenter)
        layout.addWidget(btn_RADARTEST, alignment=Qt.AlignCenter)

        central_widget.setLayout(layout)
        print("Log: Main window layout initialised")
        return central_widget  # Return the central widget

    def update_dropdown(self):
        print("Log: Updating COM port dropdown")
        ports = serial.tools.list_ports.comports()
        self.com_port_dropdown.clear()
        if ports:
            for port in ports:
                self.com_port_dropdown.addItem(f"Port: {port.device}, Port Description: {port.description}")
        print("Log: COM port dropdown updated")

    def on_yes_button_clicked(self):
        if not globalVariables.COM_PORT:
            print("No COM port selected")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No COM port selected. Please select a COM port first.")
            msg.exec_()
            return
        
        self.stack.setCurrentWidget(self.uploadPage)

    def on_no_button_clicked(self):
        if not globalVariables.COM_PORT:
            print("No COM port selected")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No COM port selected. Please select a COM port first.")
            msg.exec_()
            return
        self.MinimapWindow = NewMapping(self.stack)  # Pass the stack reference
        self.stack.addWidget(self.MinimapWindow)
        self.stack.setCurrentWidget(self.MinimapWindow)
    
    def on_IMU_button_clicked(self):
        self.stack.setCurrentWidget(self.dead_reckoning_page)

    def on_radar_button_clicked(self):
        self.stack.setCurrentWidget(self.radar_page)

    def on_test_button_clicked(self):
        if not globalVariables.COM_PORT:
            print("No COM port selected")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No COM port selected. Please select a COM port first.")
            msg.exec_()
            return
        self.stack.setCurrentWidget(self.test_page)

    def on_console_button_clicked(self):
        if not globalVariables.COM_PORT:
            print("No COM port selected")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText("No COM port selected. Please select a COM port first.")
            msg.exec_()
            return
         
        self.stack.setCurrentWidget(self.consolePage)
    
    def update_selected_com_port(self):
        selected_index = self.com_port_dropdown.currentIndex()
        if selected_index >= 0:
            globalVariables.COM_PORT = serial.tools.list_ports.comports()[selected_index]
            print(f"Log: Selected COM port: {globalVariables.COM_PORT}")

    def scan_com_port(self):
        print("Log: Scanning for COM ports")
        self.update_dropdown()
        ports = serial.tools.list_ports.comports()
        msg = QMessageBox()
        if ports:
            found_ports = [port for port in ports if globalVariables.IDENTIFIER in port.description]

            msg.setWindowTitle("COM Port Scan")

            if found_ports:
                globalVariables.COM_PORT = found_ports[0]
                msg.setIcon(QMessageBox.Information)
                found_ports = [found_port.device for found_port in found_ports]
                found_ports_str = ",".join(found_ports)
                msg.setText(f"✅ Found Device(s): {found_ports_str}🔹 Selecting COM Port: {globalVariables.COM_PORT}")
                print(f"Log: Found device(s): {found_ports_str}, selecting COM port: {globalVariables.COM_PORT}")
            else:
                msg.setIcon(QMessageBox.Warning)
                msg.setText("❌ Desired device not detected.")
                print("Log: Desired device not detected")
        else:
            msg.setIcon(QMessageBox.Warning)
            msg.setText("❌ No devices detected.")
            print("Log: No devices detected")

        msg.setText(f"<h3>{msg.text()}</h3>")
        msg.exec_()

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
            print("Log: Main Window Stylesheet applied.")
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
