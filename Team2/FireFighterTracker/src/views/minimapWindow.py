from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from controllers.minimap import FloorPlan
from widgets.titleWidget import TitleWidget

import PyQt5.QtGui as QtGui

class MinimapWindow(QWidget):
    def __init__(self, pixmap, filepath, stack):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter UAV - Processed Page")
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        self.filepath = filepath
        self.initUI(pixmap)
        self.apply_stylesheet("assets/stylesheets/base.qss")

    def initUI(self, pixmap):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        titleCard = TitleWidget("Minimap", "Floor Plan Settings", "assets/images/SFRS Logo.png")
        left_layout.addWidget(titleCard)


        # Spacer
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Settings Buttons
        ButtonLabels = ["Image Blur", "Player Size", "Trail Size", "Tile Size", "Player Size"]
        for i in range(4):
            button_layout = QHBoxLayout()
            btn_label = QLabel(ButtonLabels[i])
            btn_label.setAlignment(Qt.AlignCenter)
            btn_label.setObjectName("BtnLabel")

            btn_down = QPushButton("∨")
            btn_down.setFixedSize(30, 30)
            btn_down.setObjectName("arrows")

            btn_center = QLabel("1")
            btn_center.setFixedSize(200, 30)
            btn_center.setAlignment(Qt.AlignCenter)
            btn_center.setObjectName("miniMapSettings")

            btn_up = QPushButton("∧")
            btn_up.setFixedSize(30, 30)
            btn_up.setObjectName("arrows")

            left_layout.addWidget(btn_label)
            button_layout.addWidget(btn_down)
            button_layout.addWidget(btn_center)
            button_layout.addWidget(btn_up)
            left_layout.addLayout(button_layout)

        # Spacer
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Recreate Layout Button
        recreate_button = QPushButton("Recreate Layout")
        recreate_button.setObjectName("btnYes")
        recreate_button.setFont(QFont("Arial", 12))

        # Horizontal Line
        horizontal_line = QLabel()
        horizontal_line.setFixedSize(250, 2)
        horizontal_line.setObjectName("horizontalLine")
        horizontal_line.setAlignment(Qt.AlignCenter)

        # Back Button
        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnYes")
        btn_back.setFont(QFont("Arial", 12))
        btn_back.clicked.connect(self.open_upload_page)  # Connect to the back button

        left_layout.addWidget(horizontal_line, alignment=Qt.AlignCenter)
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        left_layout.addWidget(recreate_button, alignment=Qt.AlignCenter)
        left_layout.addWidget(btn_back, alignment=Qt.AlignCenter)

        # Right Layout for Floor Plan
        remaining_height = int(self.height()*2)
        aspect_ratio = pixmap.width() / pixmap.height()
        adjusted_width = int(self.width()*3)

        self.floor_plan_view = FloorPlan(self.filepath, width=adjusted_width, height=remaining_height, blur_effect=35)
        # self.floor_plan_view.setFixedSize(adjusted_width, remaining_height)

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