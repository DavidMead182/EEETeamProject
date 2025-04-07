import sys
import json
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                            QGraphicsScene, QVBoxLayout, QWidget, QLabel, 
                            QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, QPointF, QObject, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF, QColor

class DataConnection(QObject):
    """Abstract base class for data connections"""
    data_received = pyqtSignal(dict)
    
    def connect(self):
        raise NotImplementedError
        
    def disconnect(self):
        raise NotImplementedError

class MinimapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMU & Radar Minimap")
        self.setGeometry(100, 100, 800, 800)
        
        # Create graphics view and scene
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setSceneRect(-400, -400, 800, 800)  # Center at (0,0)
        
        # Status bar
        self.status_label = QLabel("Disconnected")
        self.data_count_label = QLabel("Packets: 0")
        self.lost_count_label = QLabel("Lost: 0")
        
        status_bar = QWidget()
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.data_count_label)
        status_layout.addWidget(self.lost_count_label)
        status_bar.setLayout(status_layout)
        
        # Set up central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(status_bar)
        central_widget.setLayout(layout)
        
        # Data storage
        self.radar_data = []
        self.imu_data = []
        self.person_trail = []
        self.current_position = QPointF(0, 0)  # Start at center
        self.current_yaw = 0
        self.packet_count = 0
        self.lost_packets = 0
        
    
        # Connection
        self.connection = None
        
        # Timer for display updates
        self.display_timer = QTimer()
        self.display_timer.timeout.connect(self.update_display)
        self.display_timer.start(50)  # Update every 50ms
        
    def set_connection(self, connection):
        """Set the data connection to use"""
        if self.connection:
            self.connection.disconnect()
            self.connection.data_received.disconnect()
        
        self.connection = connection
        self.connection.data_received.connect(self.process_data)
        self.connection.connect()
        self.status_label.setText("Connected")
        
    def process_data(self, data):
        """Process incoming JSON data"""
        try:
            # Update packet counters
            self.packet_count += 1
            self.lost_packets += data.get("packets_lost", 0)
            self.data_count_label.setText(f"Packets: {self.packet_count}")
            self.lost_count_label.setText(f"Lost: {self.lost_packets}")
            
            # Store IMU data
            self.imu_data.append(data)
            
            # Store radar distance if valid
            if "distance" in data and 0 < data["distance"] < 1000:
                self.radar_data.append((data["yaw"], data["distance"]))
                print(f"Added radar point: yaw={data['yaw']}, distance={data['distance']}")  # Debug
                
            # # Keep only recent data
            # if len(self.imu_data) > 100:
            #     self.imu_data.pop(0)
            # if len(self.radar_data) > 100:
            #     self.radar_data.pop(0)
                
            # Update position based on IMU (simplified)
            self.current_yaw = data["yaw"]
            movement_x = data.get("accel_x", 0) * 0.5  # Scale factor for visualization
            movement_y = data.get("accel_y", 0) * 0.5
            
            # Convert to global coordinates based on yaw
            rad = -math.radians(self.current_yaw)
            new_x = self.current_position.x() + (movement_x * math.cos(rad)) - (movement_y * math.sin(rad))
            new_y = self.current_position.y() + (movement_x * math.sin(rad)) + (movement_y * math.cos(rad))
            
            # Update position
            self.current_position = QPointF(new_x, new_y)
            self.person_trail.append(QPointF(new_x, new_y))
            
            # Keep trail length reasonable
            if len(self.person_trail) > 50:
                self.person_trail.pop(0)
                
        except Exception as e:
            print(f"Error processing data: {e}")
    
    def update_display(self):
        """Update the minimap display"""
        self.scene.clear()
        
        # Draw radar walls (blue)
        wall_pen = QPen(QColor(0, 0, 255), 2)
        wall_brush = QBrush(QColor(0, 0, 255, 100))  # More opaque blue
        
        for yaw, distance in self.radar_data:
            # Convert polar to cartesian coordinates (relative to person)
            rad = -math.radians(yaw)
            scaled_distance = distance / 2  # Scale down for better visibility
            x = self.current_position.x() + scaled_distance * math.cos(rad)
            y = self.current_position.y() + scaled_distance * math.sin(rad)
            
            # Draw wall point (larger size: 10x10 pixels)
            self.scene.addEllipse(x-5, y-5, 10, 10, wall_pen, wall_brush)
        
        # Draw person trail (green)
        if len(self.person_trail) > 1:
            trail_pen = QPen(QColor(0, 255, 0, 150), 2)
            path = QPolygonF(self.person_trail)
            self.scene.addPolygon(path, trail_pen)
        
        # Draw person (red circle with direction arrow)
        self.draw_person()
        
    def draw_person(self):
        """Draw the person with direction arrow"""
        person_pen = QPen(Qt.red, 2)
        person_brush = QBrush(Qt.red)
        
        # Person circle
        person_radius = 3
        self.scene.addEllipse(
            self.current_position.x() - person_radius, 
            self.current_position.y() - person_radius, 
            person_radius * 2, 
            person_radius * 2, 
            person_pen, 
            person_brush
        )
        
        # Direction arrow
        arrow_length = 20
        rad = -math.radians(self.current_yaw)
        arrow_end = QPointF(
            self.current_position.x() + arrow_length * math.cos(rad),
            self.current_position.y() + arrow_length * math.sin(rad)
        )
        
        arrow_pen = QPen(Qt.red, 2)
        self.scene.addLine(
            self.current_position.x(), 
            self.current_position.y(), 
            arrow_end.x(), 
            arrow_end.y(), 
            arrow_pen
        )
        
        # Add arrowhead
        arrow_head_size = 8
        angle = math.atan2(arrow_end.y() - self.current_position.y(), 
                          arrow_end.x() - self.current_position.x())
        
        p1 = QPointF(
            arrow_end.x() - arrow_head_size * math.cos(angle - math.pi/6),
            arrow_end.y() - arrow_head_size * math.sin(angle - math.pi/6)
        )
        p2 = QPointF(
            arrow_end.x() - arrow_head_size * math.cos(angle + math.pi/6),
            arrow_end.y() - arrow_head_size * math.sin(angle + math.pi/6)
        )
        
        arrow_head = QPolygonF([arrow_end, p1, p2])
        self.scene.addPolygon(arrow_head, arrow_pen, QBrush(Qt.white))

class SerialConnection(DataConnection):
    """Serial connection implementation"""
    def __init__(self, port, baudrate):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        
    def connect(self):
        try:
            import serial
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.status = "Connected"
            
            # Start reading thread
            self.read_timer = QTimer()
            self.read_timer.timeout.connect(self.read_data)
            self.read_timer.start(10)
            
        except Exception as e:
            print(f"Serial connection error: {e}")
            self.status = "Connection failed"
            
    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
        if hasattr(self, 'read_timer'):
            self.read_timer.stop()
        self.status = "Disconnected"
            
    def read_data(self):
        if self.serial and self.serial.in_waiting:
            try:
                line = self.serial.readline().decode('utf-8').strip()
                if line:
                    data = json.loads(line)
                    self.data_received.emit(data)
            except Exception as e:
                print(f"Error reading serial data: {e}")

class SimulatedConnection(DataConnection):
    """Simulated data connection for testing"""
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_data)
        
    def connect(self):
        self.timer.start(100)
        
    def disconnect(self):
        self.timer.stop()
        
    def generate_data(self):
        self.counter += 1
        yaw = (self.counter * 5) % 360
        distance = 100 + 50 * math.sin(math.radians(self.counter * 10))
        data = {
            "sequence": self.counter,
            "packets_lost": 0,
            "pitch": 0,
            "roll": 0,
            "yaw": yaw,
            "distance": distance,
            "accel_x": 0.1 * math.cos(math.radians(self.counter * 5)),
            "accel_y": 0.1 * math.sin(math.radians(self.counter * 5)),
            "accel_z": 9.8,
            "timestamp": self.counter
        }
        self.data_received.emit(data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MinimapApp()
    
    # Use simulated connection for demo (shows both person and radar)
    window.set_connection(SerialConnection(port='COM5', baudrate=115200))
    
    window.show()
    sys.exit(app.exec_())