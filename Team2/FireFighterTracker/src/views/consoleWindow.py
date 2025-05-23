from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                            QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui
import json
from datetime import datetime
import serial
import serial.tools.list_ports

class Console(QWidget):
    def __init__(self, text, stack):
        super().__init__()
        self.stack = stack
        self.setWindowTitle("Firefighter Tracker - MCU Data Console")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        
        # Serial connection variables
        self.serial_connection = None
        self.baudrate = 115200  # Match your MCU's baud rate
        self.max_lines = 500    # Limit console history
        
        self.initUI(text)
        self.apply_stylesheet("assets/stylesheets/base.qss")
        self.setup_serial()
        
        # Data refresh timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.read_serial_data)
        self.update_timer.start(50)  # Check for data every 50ms

    def initUI(self, text):
        layout = QVBoxLayout()
        
        # Header
        self.status_label = QLabel(f"{text} | Not connected")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Console display
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setLineWrapMode(QTextEdit.NoWrap)
        self.console.setFont(QtGui.QFont("Courier New", 9))
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.console)
        scroll.setWidgetResizable(True)
        
        # Control buttons
        btn_layout = QVBoxLayout()
        
        self.btn_connect = QPushButton("Reconnect Serial")
        self.btn_connect.clicked.connect(self.setup_serial)
        
        btn_back = QPushButton("Back to Main")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        btn_clear = QPushButton("Clear Console")
        btn_clear.clicked.connect(self.clear_console)
        
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(btn_back)
        btn_layout.addWidget(btn_clear)
        
        # Main layout
        layout.addWidget(self.status_label)
        layout.addWidget(scroll, stretch=1)
        layout.addLayout(btn_layout)
        
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
            mcu_port = "COM6"  # For testing, replace with actual port
            
            self.serial_connection = serial.Serial(
                mcu_port,
                self.baudrate,
                timeout=0.1  # Non-blocking with short timeout
            )
            self.status_label.setText(f"Connected to {mcu_port} @ {self.baudrate} baud")
            self.log_message("SYSTEM", f"Connected to {mcu_port}")
        except Exception as e:
            self.status_label.setText("Connection failed")
            self.log_message("ERROR", f"Serial connection failed: {str(e)}")

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
            self.log_message("ERROR", f"Serial read error: {str(e)}")
            self.serial_connection.close()

    def process_mcu_data(self, raw_data):
        """Parse and display MCU JSON data"""
        try:
            data = json.loads(raw_data)
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Format with syntax highlighting
            formatted_json = json.dumps(data, indent=2)
            colored_json = self.highlight_json(formatted_json)
            
            self.console.append(f"[{timestamp}] {colored_json}")
            self.ensure_scroll()
            
        except json.JSONDecodeError:
            self.log_message("ERROR", f"Invalid JSON: {raw_data}")
        except Exception as e:
            self.log_message("ERROR", f"Processing error: {str(e)}")

    def highlight_json(self, json_str):
        """Simple syntax highlighting for JSON"""
        # This is a basic implementation - extend with QTextEdit's HTML support for better highlighting
        return json_str.replace('"', '<font color="#CE9178">"</font>').replace(
            ':', '<font color="#569CD6">:</font>').replace(
            '{', '<font color="#FFD700">{</font>').replace(
            '}', '<font color="#FFD700">}</font>')

    def log_message(self, prefix, message):
        """Add system/error messages to console"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.console.append(f"[{timestamp}] <b>{prefix}:</b> {message}")
        self.ensure_scroll()

    def ensure_scroll(self):
        """Auto-scroll to bottom if not at manual scroll position"""
        scrollbar = self.console.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()
        if at_bottom or scrollbar.maximum() < 50:  # Auto-scroll if near bottom
            scrollbar.setValue(scrollbar.maximum())

    def clear_console(self):
        """Clear the console display"""
        self.console.clear()
        self.log_message("SYSTEM", "Console cleared")

    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            # Fallback styling
            self.setStyleSheet("""
                QTextEdit {
                    background-color: #1E1E1E;
                    color: #D4D4D4;
                    font-family: 'Courier New';
                    border: 1px solid #3E3E3E;
                }
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 8px;
                }
                QPushButton {
                    min-height: 30px;
                    padding: 5px;
                    margin: 3px;
                }
            """)

    def closeEvent(self, event):
        """Clean up when window closes"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.update_timer.stop()
        event.accept()