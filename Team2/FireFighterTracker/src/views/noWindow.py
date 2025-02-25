from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5 import QtGui


class NoWindow(QWidget):
    def __init__(self, text, stack):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter UAV - No Page")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        print("Log: Initialising UI.")
        self.initUI(text)
        print("Log: Applying stylesheet.")
        self.apply_stylesheet("assets/stylesheets/base.qss")

    def initUI(self, text):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)

        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))  # Navigate back to the main page

        layout.addWidget(label)
        layout.addWidget(btn_back)

        self.setLayout(layout)
        print("Log: UI initialised with text:", text)

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
            print("Log: No Window Stylesheet applied.")
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")