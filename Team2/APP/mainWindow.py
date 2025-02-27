import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QStackedWidget, QHBoxLayout, QFileDialog, QSlider, QLineEdit, QFrame
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import serial.tools.list_ports
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QComboBox


from minimap import FloorPlan


TILE_SIZE = 1  # Size of each tile
PLAYER_SIZE = 10  # Size of red dot
TRAIL_SIZE = 10  # Number of steps to keep the trail
COM_Port = None # Initially set the com port

class MainWindow(QMainWindow):

    def __init__(self):
        #print("Log: Application initiation started.")
        super().__init__()

        self.setWindowTitle("Firefighter UAV")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QtGui.QIcon("Assets/images/LOGO.png"))
        print("Log: Window created.")

        self.main_page = self.create_main_page()
        print("Log: Main page created.")

        self.page_yes = self.upload_page()
        print("Log: Upload page created.")

        self.page_no = self.create_page("No Page - Manual Setup")
        print("Log: default page created.")

        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.page_yes)
        self.stack.addWidget(self.page_no)
        print("Log: Pages added to stack.")

        self.apply_stylesheet("style.qss")
        self.showMaximized()

    def create_main_page(self):
        print("Log: Creating main page.")
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        logo.setObjectName("logo")
        pixmap = QPixmap("assets/images/SFRS Logo.png")
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("Firefighter UAV")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Do you have a floorplan?")
        subtitle.setObjectName("mainSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        btn_yes = QPushButton("Yes")
        btn_yes.setObjectName("btnYes")
        btn_yes.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_yes))

        btn_no = QPushButton("No")
        btn_no.setObjectName("btnNo")
        btn_no.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_no))

        btn_layout.addWidget(btn_yes)
        btn_layout.addWidget(btn_no)

        btn_scan_com = QPushButton("Scan USB Port For Device")
        btn_scan_com.setObjectName("btnYes")
        btn_scan_com.setFixedWidth(350)
        btn_scan_com.setFixedHeight(40)
        btn_scan_com.clicked.connect(self.scan_com_port)

        self.com_port_dropdown = QComboBox()
        self.com_port_dropdown.setObjectName("comPortDropdown")
        self.com_port_dropdown.setEditable(False)
        self.com_port_dropdown.activated.connect(self.update_selected_com_port)
        self.com_port_dropdown.setFixedWidth(350)
        self.com_port_dropdown.setFixedHeight(40)



        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(btn_layout)

        layout.addWidget(btn_scan_com, alignment=Qt.AlignCenter)
        layout.addWidget(self.com_port_dropdown, alignment=Qt.AlignCenter)

        page.setLayout(layout)
        return page

    def upload_page(self):
        print("Log: Creating upload page.")
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        logo = QLabel()
        logo.setObjectName("logo")
        pixmap = QPixmap("assets/images/SFRS Logo.png")
        logo.setPixmap(pixmap)
        logo.setAlignment(Qt.AlignCenter)

        title = QLabel("Firefighter UAV")
        title.setObjectName("mainTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Upload your floor plan")
        subtitle.setObjectName("mainSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        btn_upload = QPushButton("Upload")
        btn_upload.setObjectName("btnYes")

        self.upload_Image = QLabel("")
        self.upload_Image.setFixedSize(700, 400)
        self.upload_Image.setScaledContents(False)
        btn_upload.clicked.connect(self.upload_image)

        self.process_button = QPushButton("Create Map")
        self.process_button.setObjectName("btnYes")
        self.process_button.setVisible(False)
        self.process_button.clicked.connect(self.process_image)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnYes")
        btn_back.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_page))

        layout.addWidget(logo)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(btn_upload)
        layout.addWidget(self.upload_Image)
        layout.addWidget(self.process_button) 
        layout.addWidget(btn_back)

        page.setLayout(layout)
        return page

    def process_image(self):
        print("Log: switching to minimap page")
        self.page_processed = self.create_processed_page(self.upload_Image.pixmap())
        self.stack.addWidget(self.page_processed)
        self.stack.setCurrentWidget(self.page_processed)

    def create_processed_page(self, pixmap):
        print("Log: Creating minimap page.")
        page = QWidget()
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
        #recreate_button.clicked.connect()

        horizontal_line = QLabel()
        horizontal_line.setFixedSize(250,5)
        horizontal_line.setObjectName("horizontalLine")
        horizontal_line.setAlignment(Qt.AlignCenter)

        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnYes")
        btn_back.clicked.connect(lambda: self.stack.setCurrentWidget(self.page_yes))

        left_layout.addWidget(horizontal_line,alignment= Qt.AlignCenter)

        left_layout.addWidget(recreate_button,alignment= Qt.AlignCenter)
        left_layout.addWidget(btn_back,alignment= Qt.AlignCenter)

        # Adjust the height to the remaining height and width based on the aspect ratio of the image
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

        page.setLayout(layout)
        return page
    
    def update_dropdown(self):
        ports = serial.tools.list_ports.comports()
        self.com_port_dropdown.clear()
        if ports:
            for port in ports:
                self.com_port_dropdown.addItem(f"Port: {port.device}, Port Description: {port.description}")
    
    def update_selected_com_port(self):
        selected_index = self.com_port_dropdown.currentIndex()
        if selected_index >= 0:  
            COM_Port = serial.tools.list_ports.comports()[selected_index]

    def scan_com_port(self):
        self.update_dropdown()
        ports = serial.tools.list_ports.comports()
        if ports:
            identifier = "USB Serial Device"
            found_ports = [port for port in ports if identifier in port.description]
            
            msg = QMessageBox()
            msg.setWindowTitle("COM Port Scan")

            if found_ports:
                COM_Port = found_ports[0]
                msg.setIcon(QMessageBox.Information)
                found_ports = [found_port.device for found_port in found_ports]
                found_ports_str = ",".join(found_ports)  
                msg.setText(f"✅ Found Device(s): {found_ports_str}🔹 Selecting COM Port: {COM_Port}")
            else:
                msg.setIcon(QMessageBox.Warning)
                msg.setText("❌ Desired device not detected.")
        else:
            msg.setIcon(QMessageBox.Warning)
            msg.setText("❌ No devices detected.")

        msg.setText(f"<h3>{msg.text()}</h3>")   

        msg.exec_()


    def create_page(self, text):
        print("Log: Creating default page.")
        page = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)

        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.stack.setCurrentWidget(self.main_page))

        layout.addWidget(label)
        layout.addWidget(btn_back)

        page.setLayout(layout)
        return page

    def upload_image(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "Images (*.png *.xpm *.jpg *.jpeg *.bmp)", options=options)
        if file_name:
            pixmap = QtGui.QPixmap(file_name)
            self.upload_Image.setPixmap(pixmap.scaled(self.upload_Image.size(), QtCore.Qt.KeepAspectRatio))
            print("Log: Image uploaded.")
            self.process_button.setVisible(True)
            print("Log: Create minimap Button visible.")

    

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
            print("Log: Stylesheet applied.")
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("Log: app created")
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

