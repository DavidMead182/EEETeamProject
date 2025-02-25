import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QStackedWidget, QHBoxLayout, QFileDialog, QSlider, QLineEdit, QFrame
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import serial.tools.list_ports
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox


from controllers.minimap import FloorPlan
from widgets.titleWidget import TitleWidget



TILE_SIZE = 1  # Size of each tile
PLAYER_SIZE = 10  # Size of red dot
TRAIL_SIZE = 10  # Number of steps to keep the trail
COM_Port = None # Initially set the com port

class UploadWindow(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter UAV - Upload Page")
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        self.initUI()
        self.apply_stylesheet("assets/stylesheets/base.qss")
        self.showMaximized()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        titleCard = TitleWidget("Firefighter UAV", "Upload your floor plan", "assets/images/SFRS Logo.png")

        btn_upload = QPushButton("Upload")
        btn_upload.setObjectName("btnYes")
        btn_upload.clicked.connect(self.upload_image)

        self.upload_Image = QLabel("")
        self.upload_Image.setFixedSize(700, 400)
        self.upload_Image.setScaledContents(False)

        self.process_button = QPushButton("Create Map")
        self.process_button.setObjectName("btnYes")
        self.process_button.setVisible(False)
        self.process_button.clicked.connect(self.process_image)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnYes")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))  # Navigate back to the main page

        layout.addWidget(titleCard)
        layout.addWidget(btn_upload)
        layout.addWidget(self.upload_Image)
        layout.addWidget(self.process_button)
        layout.addWidget(btn_back)

        self.setLayout(layout)

    def upload_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)", options=options)
        if file_name:
            pixmap = QtGui.QPixmap(file_name)
            self.upload_Image.setPixmap(pixmap.scaled(self.upload_Image.size(), QtCore.Qt.KeepAspectRatio))
            self.process_button.setVisible(True)

    def process_image(self):
        from views.minimapWindow import MinimapWindow
        # Create a new MinimapWindow with the uploaded image
        self.minimap_page = MinimapWindow(self.upload_Image.pixmap(), self.stack)
        self.stack.addWidget(self.minimap_page)  # Add the new page to the stack
        self.stack.setCurrentWidget(self.minimap_page)  # Navigate to the new page

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
            print("Log: Stylesheet applied.")
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
