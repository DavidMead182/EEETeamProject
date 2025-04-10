from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui,QtCore
from PyQt5.QtGui import QPixmap, QFont
import json
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import math
from widgets.titleWidget import TitleWidget
import pyqtgraph as pg
import numpy as np

class NewMapping(QWidget):
    def __init__(self, stack):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter UAV - No Page")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        
        # Serial connection variables
        self.serial_connection = None
        self.baudrate = 115200  # Set to match the MCU's baud rate
        
        # Timer for data updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.read_serial_data)
        self.update_timer.start(50)  # Check for data every 50ms
        
        # Placeholder for displaying data
        self.data = {
            "sequence": 0, "packets_lost": 0, "pitch": 0, "roll": 0,
            "yaw": 0, "distance": 0, "accel_x": 0, "accel_y": 0,
            "accel_z": 0, "timestamp": 0
        }
        
        # Data buffers for plotting
        self.time_data = []
        self.accel_x_data = []
        self.accel_y_data = []
        self.accel_z_data = []
        self.x_position_data = [0]
        self.y_position_data = [0]
        self.radar_x_data = [0]
        self.radar_y_data = [0]
        
        self.initUI()
        self.apply_stylesheet("assets/stylesheets/base.qss")
        self.setup_serial()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)

        titleCard = TitleWidget("Minimap", "Floor Plan Settings", "assets/images/SFRS Logo.png")
        left_layout.addWidget(titleCard)

        self.graphWidget = pg.PlotWidget()
        self.x = list(range(100))  # X-axis (time)
        self.y = [0] * 100         # Y-axis (data)
 
        self.data_line = self.graphWidget.plot(self.x, self.y, pen=pg.mkPen(color='c', width=2))
 
        # Timer to update the plot
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)  # milliseconds
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))  # Navigate back to the main page
        btn_back.setObjectName("btnYes")
        btn_back.setFont(QFont("Arial", 12))

        right_layout.addWidget(self.graphWidget)
        # Add widgets to layout
        left_layout.addWidget(btn_back)
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        self.setLayout(layout)

    def update_plot_data(self):
        new_val = np.random.normal()  # replace with your real-time data
        self.y = self.y[1:] + [new_val]  # shift data
        self.data_line.setData(self.x, self.y)

    def setup_serial(self):
        """Initialize or reinitialize serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        
        try:
            ports = serial.tools.list_ports.comports()
            if not ports:
                raise Exception("No serial ports found")
                
            # Try to automatically find the MCU (adjust filters as needed)
            mcu_port = None
            for port in ports:
                if "USB" in port.description or "ACM" in port.device:
                    mcu_port = port.device
                    break
            
            if not mcu_port:
                mcu_port = ports[0].device  # Fallback to first port
            
            self.serial_connection = serial.Serial(
                mcu_port,
                self.baudrate,
                timeout=0.1  # Non-blocking with short timeout
            )
            print(f"Log: Connected to {mcu_port} @ {self.baudrate} baud")
        except Exception as e:
            print(f"Log: Serial connection failed: {str(e)}")

    def read_serial_data(self):
        """Read and process incoming serial data"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return
            
        try:
            while self.serial_connection.in_waiting > 0:
                raw_data = self.serial_connection.readline().decode('utf-8').strip()
                if raw_data:
                    self.process_mcu_data(raw_data)
        except Exception as e:
            print(f"Log: Serial read error: {str(e)}")
            self.serial_connection.close()

    def process_mcu_data(self, raw_data):
        """Parse and display MCU JSON data"""
        try:
            data = json.loads(raw_data)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Format the data for display in the label
            data_text = f"Timestamp: {timestamp}\n"
            data_text += f"Sequence: {data['sequence']}\n"
            data_text += f"Packets Lost: {data['packets_lost']}\n"
            data_text += f"Pitch: {data['pitch']:.3f}\n"
            data_text += f"Roll: {data['roll']:.3f}\n"
            data_text += f"Yaw: {data['yaw']:.3f}\n"
            data_text += f"Distance: {data['distance']:.2f} m\n"
            data_text += f"Accel X: {data['accel_x']:.3f} m/s²\n"
            data_text += f"Accel Y: {data['accel_y']:.3f} m/s²\n"
            data_text += f"Accel Z: {data['accel_z']:.3f} m/s²\n"

            # Update the label with new data
            self.data_label.setText(data_text)
            
            # Update internal data
            self.data = data

            # Add the new data to the plot buffers
            current_time = datetime.now().timestamp()  # Current time in seconds
            self.time_data.append(current_time)
            self.accel_x_data.append(data['accel_x'])
            self.accel_y_data.append(data['accel_y'])
            self.accel_z_data.append(data['accel_z'])
            
            # Update person position (for tracking)
            distance = data['distance']
            yaw = math.radians(data['yaw'])  # Convert yaw to radians
            dx = distance * math.cos(yaw)  # X displacement
            dy = distance * math.sin(yaw)  # Y displacement
            self.x_position_data.append(self.x_position_data[-1] + dx)
            self.y_position_data.append(self.y_position_data[-1] + dy)

            # Update radar position
            self.radar_x_data.append(self.x_position_data[-1])
            self.radar_y_data.append(self.y_position_data[-1])

            # Update the plots
            self.update_plots()

        except json.JSONDecodeError:
            print(f"Log: Invalid JSON: {raw_data}")
        except Exception as e:
            print(f"Log: Processing error: {str(e)}")

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
