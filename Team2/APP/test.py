import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtGui import QPixmap

class MiniMapApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Left panel
        left_panel = QVBoxLayout()
        
        # Logo
        logo = QLabel(self)
        logo.setObjectName("logo")
        pixmap_logo = QPixmap("assets/images/SFRS Logo.png")
        logo.setPixmap(pixmap_logo)
        left_panel.addWidget(logo)

        # Title
        title = QLabel("Mini Map")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        left_panel.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Floor plan Settings")
        subtitle.setStyleSheet("font-size: 16px; color: gray;")
        left_panel.addWidget(subtitle)
        
        # Upload buttons
        for _ in range(6):
            btn = QPushButton("Upload")
            left_panel.addWidget(btn)
        
        left_panel.setSpacing(10)

        # Right panel (Mini Map)
        right_panel = QFrame()
        right_panel.setStyleSheet("background-color: lightgray;")
        right_panel.setFixedSize(600, 400)
        mini_map_label = QLabel("Mini Map", right_panel)
        mini_map_label.setStyleSheet("font-size: 14px;")
        mini_map_label.move(280, 190)
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_panel)
        main_layout.addWidget(right_panel)
        
        self.setLayout(main_layout)
        self.setWindowTitle("Mini Map Viewer")
        self.setGeometry(100, 100, 800, 500)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MiniMapApp()
    window.show()
    sys.exit(app.exec_())
