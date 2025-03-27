from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt
from controllers.minimap import FloorPlan
from widgets.titleWidget import TitleWidget

import PyQt5.QtGui as QtGui

class MinimapWindow(QWidget):
    def __init__(self, pixmap, filepath, stack):
        super().__init__()
        self.stack = stack
        self.setWindowTitle("Firefighter UAV - Processed Page")
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        self.filepath = filepath
        
        # Initialize settings values
        self.player_size = 10
        self.tile_size = 1
        self.trail_size = 5
        self.blur_effect = 35
        
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

        # Settings Controls
        self.create_setting_controls(left_layout)

        # Spacer
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Recreate Layout Button
        recreate_button = QPushButton("Recreate Layout")
        recreate_button.setObjectName("btnYes")
        recreate_button.setFont(QFont("Arial", 12))
        recreate_button.clicked.connect(self.recreate_layout)

        # Horizontal Line
        horizontal_line = QLabel()
        horizontal_line.setFixedSize(250, 2)
        horizontal_line.setObjectName("horizontalLine")
        horizontal_line.setAlignment(Qt.AlignCenter)

        # Back Button
        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnYes")
        btn_back.setFont(QFont("Arial", 12))
        btn_back.clicked.connect(self.open_upload_page)

        left_layout.addWidget(horizontal_line, alignment=Qt.AlignCenter)
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        left_layout.addWidget(recreate_button, alignment=Qt.AlignCenter)
        left_layout.addWidget(btn_back, alignment=Qt.AlignCenter)

        # Right Layout for Floor Plan
        remaining_height = int(self.height()*2)
        adjusted_width = int(self.width()*3)

        self.floor_plan_view = FloorPlan(
            self.filepath, 
            width=adjusted_width, 
            height=remaining_height, 
            blur_effect=self.blur_effect,
            player_size=self.player_size,
            tile_size=self.tile_size,
            trail_size=self.trail_size
        )

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.floor_plan_view, alignment=Qt.AlignCenter)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        self.setLayout(layout)

    def create_setting_controls(self, layout):
        """Create all setting controls"""
        # Blur Setting
        self.add_setting_control(layout, "Image Blur", "blur", self.blur_effect, 5)
        
        # Player Size Setting
        self.add_setting_control(layout, "Player Size", "player", self.player_size, 1)
        
        # Trail Size Setting
        self.add_setting_control(layout, "Trail Size", "trail", self.trail_size, 1)
        
        # Tile Size Setting
        self.add_setting_control(layout, "Tile Size", "tile", self.tile_size, 1)

    def add_setting_control(self, parent_layout, label_text, setting_name, initial_value, step):
        """Add a single setting control"""
        # Create label
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("BtnLabel")
        parent_layout.addWidget(label)

        # Create control layout
        control_layout = QHBoxLayout()

        # Decrease button
        btn_down = QPushButton("∨")
        btn_down.setFixedSize(30, 30)
        btn_down.setObjectName("arrows")
        btn_down.clicked.connect(lambda: self.adjust_setting(setting_name, -step))
        

        # Value display
        value_label = QLabel(str(initial_value))
        value_label.setFixedSize(200, 30)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setObjectName("miniMapSettings")
        setattr(self, f"{setting_name}_value", value_label)

        # Increase button
        btn_up = QPushButton("∧")
        btn_up.setFixedSize(30, 30)
        btn_up.setObjectName("arrows")
        btn_up.clicked.connect(lambda: self.adjust_setting(setting_name, step))

        # Add to layout
        control_layout.addWidget(btn_down)
        control_layout.addWidget(value_label)
        control_layout.addWidget(btn_up)
        parent_layout.addLayout(control_layout)

    def adjust_setting(self, setting, delta):
        """Adjust the specified setting by delta and update the display"""
        if setting == "blur":
            self.blur_effect = max(0, self.blur_effect + delta)
            self.blur_value.setText(str(self.blur_effect))
            print("Log: Blur effect changed to", self.blur_effect)
        elif setting == "player":
            self.player_size = max(1, self.player_size + delta)
            self.player_value.setText(str(self.player_size))
            print("Log: Player size changed to", self.player_size)
        elif setting == "trail":
            self.trail_size = max(1, self.trail_size + delta)
            self.trail_value.setText(str(self.trail_size))
            print("Log: Trail size changed to", self.trail_size)
        elif setting == "tile":
            self.tile_size = max(1, self.tile_size + delta)
            self.tile_value.setText(str(self.tile_size))
            print("Log: Tile size changed to", self.tile_size)

    def recreate_layout(self):
        """Recreate the floor plan with current settings"""
        # Remove current floor plan
        self.layout().removeWidget(self.floor_plan_view)
        self.floor_plan_view.deleteLater()
        
        # Create new floor plan
        remaining_height = int(self.height()*2)
        adjusted_width = int(self.width()*3)
        
        self.floor_plan_view = FloorPlan(
            self.filepath, 
            width=adjusted_width, 
            height=remaining_height, 
            blur_effect=self.blur_effect,
            player_size=self.player_size,
            tile_size=self.tile_size,
            trail_size=self.trail_size
        )
        
        # Add back to layout
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.floor_plan_view, alignment=Qt.AlignCenter)
        self.layout().insertLayout(1, right_layout)

    def open_upload_page(self):
        """Return to upload page"""
        self.stack.removeWidget(self)
        self.stack.setCurrentIndex(1)

    def apply_stylesheet(self, filename):
        """Apply stylesheet to window"""
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Stylesheet not found. Using default styles.")