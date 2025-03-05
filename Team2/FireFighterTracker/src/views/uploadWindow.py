from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QVBoxLayout, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import global_variables 

from views.minimapWindow import MinimapWindow
from widgets.titleWidget import TitleWidget

class UploadWindow(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack
        self.filePath = None  # Initialize filePath to None
        self.initUI()
        self.apply_stylesheet("assets/stylesheets/base.qss")

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        titleCard = TitleWidget("Firefighter UAV", "Upload your floor plan", "assets/images/SFRS Logo.png")

        btn_upload = QPushButton("Upload")
        btn_upload.setObjectName("btnYes")
        btn_upload.clicked.connect(self.open_file_dialog)

        self.upload_Image = QLabel("")
        self.upload_Image.setFixedSize(700, 400)
        self.upload_Image.setScaledContents(True)

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

    def open_file_dialog(self):
        # Open a file dialog to select an image file
        print(global_variables.COM_PORT)
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open Image File", "", "Images (*.png *.jpg *.bmp *jpeg)", options=options
        )
        if file_name:
            self.filePath = file_name  # Set the filePath attribute
            # Load the selected image into the QLabel
            self.upload_Image.setPixmap(QPixmap(self.filePath))
            self.upload_Image.setText("")  # Clear the placeholder text
            self.process_button.setVisible(True)

    def process_image(self):
        # Check if a file has been selected
        if not hasattr(self, 'filePath') or self.filePath is None:
            print("No file has been selected.")
            return

        # Process the image (example: pass it to the MinimapWindow)
        self.minimap_page = MinimapWindow(self.upload_Image.pixmap(), self.filePath, self.stack)
        # Optionally, switch to the minimap page in the stack
        self.stack.addWidget(self.minimap_page)
        self.stack.setCurrentWidget(self.minimap_page)

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
            print("Log: Upload Window Stylesheet applied.")
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
