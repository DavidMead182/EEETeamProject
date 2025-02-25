from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from controllers.minimap import FloorPlan

import PyQt5.QtGui as QtGui

class MinimapWindow(QWidget):
    def __init__(self, pixmap, stack):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter UAV - Processed Page")
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        self.initUI(pixmap)
        self.apply_stylesheet("assets/stylesheets/base.qss")

    def initUI(self, pixmap):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        logo = QLabel()
        logo.setObjectName("logo")
        pixmap_logo = QPixmap("assets/images/SFRS Logo.png")
        logo.setPixmap(pixmap_logo)
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("Mini Map")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Floor plan Settings")
        subtitle.setObjectName("mainSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(logo)
        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)

        ButtonLabels = ["Image Blur", "Player Size", "Trail Size", "Tile Size", "Player Size"]
        for i in range(4):
            button_layout = QHBoxLayout()
            btn_label = QLabel(ButtonLabels[i])
            btn_label.setAlignment(Qt.AlignCenter)
            btn_label.setObjectName("BtnLabel")

            btn_down = QPushButton("∨")
            btn_down.setFixedSize(40, 40)
            btn_down.setObjectName("arrows")

            btn_center = QLabel("1")
            btn_center.setFixedSize(200, 40)
            btn_center.setAlignment(Qt.AlignCenter)
            btn_center.setObjectName("miniMapSettings")

            btn_up = QPushButton("∧")
            btn_up.setFixedSize(40, 40)
            btn_up.setObjectName("arrows")

            left_layout.addWidget(btn_label)
            button_layout.addWidget(btn_down)
            button_layout.addWidget(btn_center)
            button_layout.addWidget(btn_up)
            left_layout.addLayout(button_layout)

        recreate_button = QPushButton("Recreate Layout")
        recreate_button.setObjectName("btnYes")

        horizontal_line = QLabel()
        horizontal_line.setFixedSize(250, 5)
        horizontal_line.setObjectName("horizontalLine")
        horizontal_line.setAlignment(Qt.AlignCenter)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnYes")
        btn_back.clicked.connect(self.open_upload_page)  # Connect to the back button

        left_layout.addWidget(horizontal_line, alignment=Qt.AlignCenter)
        left_layout.addWidget(recreate_button, alignment=Qt.AlignCenter)
        left_layout.addWidget(btn_back, alignment=Qt.AlignCenter)

        remaining_height = self.height()
        remaining_height = int(remaining_height)
        aspect_ratio = pixmap.width() / pixmap.height()
        adjusted_width = int(remaining_height * aspect_ratio)

        self.floor_plan_view = FloorPlan(floor_plan_path="Assets/images/floorplan.jpeg", width=adjusted_width, height=remaining_height, blur_effect=35)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.floor_plan_view, alignment=Qt.AlignCenter)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        self.setLayout(layout)

    def open_upload_page(self):
        # Remove the current page from the stack
        self.stack.removeWidget(self)
        # Navigate back to the previous page (UploadWindow)
        self.stack.setCurrentIndex(1)  # Assuming UploadWindow is at index 1

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
            print("Log: Stylesheet applied.")
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")