from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui
import json
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import math

class NoWindow(QWidget):
    def __init__(self, text, stack):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter Tracker - No Page")
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
        
        self.initUI(text)
        self.apply_stylesheet("assets/stylesheets/base.qss")
        self.setup_serial()

    def initUI(self, text):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Display data label
        self.data_label = QLabel("Waiting for data...")
        self.data_label.setAlignment(Qt.AlignCenter)
        
        btn_back = QPushButton("Back")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))  # Navigate back to the main page

        # Create the plot area with two graphs stacked vertically
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6), dpi=100)

        # Setup IMU data graph (accel_x, accel_y, accel_z)
        self.ax2.set_title("IMU Data (Acceleration)")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Acceleration (m/s²)")
        self.ax2.legend(["Accel X", "Accel Y", "Accel Z"])

        # Setup Tracking graph (X, Y position)
        self.ax1.set_title("Tracking (Position)")
        self.ax1.set_xlabel("X Position (m)")
        self.ax1.set_ylabel("Y Position (m)")
        
        # Add widgets to layout
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.data_label)
        layout.addWidget(self.canvas)
        layout.addWidget(btn_back)

        self.setLayout(layout)

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

    def update_plots(self):
        """Update the plots with new data"""
        # IMU Data plot
        self.ax2.clear()
        self.ax2.plot(self.time_data, self.accel_x_data, label="Accel X", color='r')
        self.ax2.plot(self.time_data, self.accel_y_data, label="Accel Y", color='g')
        self.ax2.plot(self.time_data, self.accel_z_data, label="Accel Z", color='b')
        self.ax2.set_title("IMU Data (Acceleration)")
        self.ax2.set_xlabel("Time (s)")
        self.ax2.set_ylabel("Acceleration (m/s²)")
        self.ax2.legend()

        # Tracking (Position) plot
        self.ax1.clear()
        self.ax1.plot(self.x_position_data, self.y_position_data, label="Position", color='m')
        self.ax1.set_title("Tracking (Position)")
        self.ax1.set_xlabel("X Position (m)")
        self.ax1.set_ylabel("Y Position (m)")


        # Redraw the canvas
        self.canvas.draw()

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")
