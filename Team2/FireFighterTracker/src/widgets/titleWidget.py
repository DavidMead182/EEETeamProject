from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class TitleWidget(QWidget):
    def __init__(self, title, subtitle, image_path="../assets/images/SFRS Logo.png"):
        super().__init__()
        self.title = title
        self.subtitle = subtitle
        self.image_path = image_path
        self.initWidget()

    def initWidget(self):
        # Create a layout for the TitleWidget
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Add the logo
        logo = QLabel()
        logo.setObjectName("logo")
        pixmap = QPixmap(self.image_path)
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)

        # Add the title
        title = QLabel(self.title)
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Add the subtitle
        subtitle = QLabel(self.subtitle)
        subtitle.setObjectName("mainSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        # Set the layout for the TitleWidget
        self.setLayout(layout)