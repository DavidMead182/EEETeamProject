from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy, QSlider
from PyQt5.QtGui import QFont
from widgets.titleWidget import TitleWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtGui import QPolygonF
from PyQt5 import QtGui
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView
import json
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import math

class IncrementalLinearRegression:
    def __init__(self,start_point_x,start_point_y,scene,line_radius=50):
        self.n = 0
        self.Sx = 0.0
        self.Sy = 0.0
        self.Sxx = 0.0
        self.Sxy = 0.0
        self.slope = 0.0
        self.intercept = 0.0
        self.end_points = [(start_point_x,start_point_y),(start_point_x,start_point_y)]
        self.line_radius = line_radius
        self.line_item = None
        self.scene = scene
        self.initial_x = start_point_x
        self.initial_y = start_point_y
        self.angle_tolerance = 1
        self.starting_angle_tolerance = 90
        self.slope_learning_rate = 1
        self.number_of_points_for_established_trend = 10

    def add_point(self, x, y):
        self.n += 1
        self.Sx += x
        self.Sy += y
        self.Sxx += x * x
        self.Sxy += x * y

        if self.n >= 2:
            denominator = self.n * self.Sxx - self.Sx ** 2
            if denominator != 0:
                new_slope = (self.n * self.Sxy - self.Sx * self.Sy) / denominator
                if self.n>2:
                    current_angle = math.atan(self.slope)
                    new_angle = math.atan(new_slope)
                    angle_diff = abs(current_angle - new_angle)

                    base_threshold = math.radians(self.starting_angle_tolerance)
                    k = self.slope_learning_rate
                    min_angle_tolerance = math.radians(self.angle_tolerance)  
                    tolerance = max(min_angle_tolerance, base_threshold * math.exp(-k * (self.n - 2)))

                    if angle_diff > tolerance:
                        return False  

                self.slope = new_slope
                self.intercept = (self.Sy - self.slope * self.Sx) / self.n
            
        if self.n > 2:
            self.update_end_points(x,y,self.n>self.number_of_points_for_established_trend)
        else:
            self.end_points[1] = (x,y)
        
        if self.n>=2:
            self.draw_line()
        return True

    def predict(self, x):
        return self.slope * x + self.intercept
    
    def predict_x(self, y):
        if self.slope != 0:
            return (y - self.intercept) / self.slope
        else:
            return self.initial_x
    
    def in_boundary(self,x,y):
        (x0, y0), (x1, y1) = self.end_points

        if x > min(x0, x1) and x < max(x0, x1) and y > min(y0, y1) and y < max(y0, y1):
            return True
        else:
            return False
        
    def find_relevant_end_point(self,x,y):
        distance = math.sqrt((x - self.end_points[0][0]) ** 2 + (y - self.end_points[0][1]) ** 2),math.sqrt((x - self.end_points[1][0]) ** 2 + (y - self.end_points[1][1]) ** 2)
        index = 0 if distance[0] < distance[1] else 1
        return index
    
    def in_line_radius(self,x,y,multiplier=1):
        line_radius = self.line_radius*multiplier
        if self.n >= 2:
            if self.in_boundary(x,y):
                distance = math.sqrt((x - self.predict_x(y)) ** 2 + (y - self.predict(x)) ** 2)
            else:
                distance = min(math.sqrt((x - self.end_points[0][0]) ** 2 + (y - self.end_points[0][1]) ** 2),math.sqrt((x - self.end_points[1][0]) ** 2 + (y - self.end_points[1][1]) ** 2))
        else:   
            distance = math.sqrt((x - self.initial_x) ** 2 + (y - self.initial_y) ** 2) 

        
        return distance < line_radius
        
    def update_end_points(self, x, y,established_trend=False): 
        if (self.in_boundary(x,y))==False:
            relevant_end_point = self.find_relevant_end_point(x, y)
        
            x1, y1 = self.end_points[relevant_end_point]
            
            # Handle the case where the x-values are equal to avoid division by zero
            if x == x1:
                slope_to_new_point = float('inf')  # or use None or a special value for vertical line
            else:
                slope_to_new_point = (y - y1) / (x - x1)
            accept = False
            if established_trend:
                current_angle = math.atan(self.slope)
                new_angle = math.atan(slope_to_new_point)
                angle_diff = abs(current_angle - new_angle)

                if angle_diff<math.radians(60):
                    accept = True

            if not established_trend or accept:
                if (self.slope ** 2) < 1:
                    new_y = self.predict(x)
                    new_point = (self.predict_x(new_y), new_y)
                else:
                    new_x = self.predict_x(y)
                    new_point = (new_x, self.predict(new_x))
                self.end_points[relevant_end_point] = new_point
                
                        

    def draw_line(self): 
        self.erase_line()

        wall_pen = QPen(QColor(0, 0, 255), 2)  # Blue

        (x0, y0), (x1, y1) = self.end_points
        self.line_item = self.scene.addLine(x0, y0, x1, y1, wall_pen)
    
    def erase_line(self):
        if self.line_item:
            self.scene.removeItem(self.line_item)
            self.line_item = None

    def combine_lines(self,other):
        self.n += other.n
        self.Sx += other.Sx
        self.Sy += other.Sy
        self.Sxx += other.Sxx
        self.Sxy += other.Sxy

        denominator = self.n * self.Sxx - self.Sx**2
        if denominator != 0:
            self.slope = (self.n * self.Sxy - self.Sx * self.Sy) / denominator
            self.intercept = (self.Sy - self.slope * self.Sx) / self.n

        other.erase_line()
        self.update_end_points(other.end_points[0][0],other.end_points[0][1])
        self.update_end_points(other.end_points[1][0],other.end_points[1][1])
        self.draw_line()
    
    def can_combine_lines(self,other):
        temp_n = self.n + other.n
        tempSx = self.Sx + other.Sx
        tempSy = self.Sy + other.Sy
        tempSxx = self.Sxx + other.Sxx
        tempSxy = self.Sxy + other.Sxy

        if temp_n >= 2:
            denominator = temp_n * tempSxx - tempSx ** 2
            if denominator != 0:
                new_slope = (temp_n * tempSxy - tempSx * tempSy) / denominator

                self_current_angle = math.atan(self.slope)
                other_current_angle = math.atan(other.slope)
                new_angle = math.atan(new_slope)
                self_angle_diff = abs(self_current_angle - new_angle)
                other_angle_diff = abs(other_current_angle - new_angle)

                base_threshold = math.radians(self.starting_angle_tolerance)
                k = self.slope_learning_rate
                min_angle_tolerance = math.radians(self.angle_tolerance)
                tolerance = max(min_angle_tolerance, base_threshold * math.exp(-k * (temp_n - 2)))

                if self_angle_diff > tolerance or other_angle_diff >tolerance:
                    return False
        
        return True
    
    # returns true if the "other" line is merged into the "self" line
    def connect_lines(self, other):
        min_distance = float('inf')
        closest_pair = None

        for end_self in self.end_points:
            for end_other in other.end_points:
                distance = math.sqrt((end_self[0] - end_other[0]) ** 2 + (end_self[1] - end_other[1]) ** 2)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (end_self, end_other)
        
        if self.in_line_radius(closest_pair[1][0],closest_pair[1][1]):
            if self.can_combine_lines(other):
                self.combine_lines(other)
                return True
            
        if other.n<2 and self.n<2:
            return False
        
        if self.slope == other.slope:
            return False

        # Calculate intersection point of two lines: y = m1*x + c1 and y = m2*x + c2
        try:
            x_intersect = (other.intercept - self.intercept) / (self.slope - other.slope)
            y_intersect = self.slope * x_intersect + self.intercept
            intersection_point = (x_intersect, y_intersect)
        except ZeroDivisionError:
            return False
        if self.in_line_radius(intersection_point[0],intersection_point[1],multiplier=2) and other.in_line_radius(intersection_point[0],intersection_point[1],multiplier = 2) and other.n>5 and self.n>5:
            self.add_point(intersection_point[0],intersection_point[1])
            other.add_point(intersection_point[0],intersection_point[1])
        return False


class DataConnection(QObject):
    """Abstract base class for data connections"""
    data_received = pyqtSignal(dict)
    
    def connect(self):
        raise NotImplementedError
        
    def disconnect(self):
        raise NotImplementedError



class NewMapping(QWidget):
    def __init__(self, stack, text="None"):
        super().__init__()
        self.stack = stack  # Store the reference to the stack
        self.setWindowTitle("Firefighter Tracker - No Page")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QtGui.QIcon("assets/icons/LOGO.png"))
        
        # Serial connection variables
        self.serial_connection = None
        self.baudrate = 115200  # Set to match the MCU's baud rate
        
        
                # Data storage
        self.radar_data = []
        self.imu_data = []
        self.person_trail = []
        self.current_position = QPointF(0, 0)  # Start at center
        self.current_yaw = 0
        self.packet_count = 0
        self.lost_packets = 0
        self.person_graphics = []
        self.prev_point = None
        self.last_timestamp = None
        self.velocity_x = 0
        self.velocity_y = 0
        self.position_x = 0
        self.position_y = 0

        # Connection
        self.connection = None

        self.lines = []

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setAlignment(Qt.AlignCenter)
        self.view.setFixedSize(1250, 900)  # Adjust size as needed
        # Set scene rect so (0,0) is at the center of the view
        width = self.view.width()
        height = self.view.height()
        self.scene.setSceneRect(-width // 2, -height // 2, width, height)
        self.view.scale(1, -1)  # Flip y-axis to match typical Cartesian plane

        self.initUI(text)
        self.set_connection(SerialConnection(port=self.get_com_port(), baudrate=115200))

    def initUI(self, text):

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        titleCard = TitleWidget("No Floorplan", "Data information", "assets/images/SFRS Logo.png")
        left_layout.addWidget(titleCard)
        # Spacer
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))


        # self.status_label = QLabel("Disconnected")
        # self.data_count_label = QLabel("Packets: 0")
        # self.lost_count_label = QLabel("Lost: 0")

        # left_layout.addWidget(self.status_label)
        # left_layout.addWidget(self.data_count_label)
        # left_layout.addWidget(self.lost_count_label)
        # Spacer
        left_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Horizontal Line
        horizontal_line = QLabel()
        horizontal_line.setFixedSize(250, 2)
        horizontal_line.setObjectName("horizontalLine")
        horizontal_line.setAlignment(Qt.AlignCenter)


        font = QFont("Arial", 12)

        self.imu_label = QLabel("Pitch: --  Roll: --  Yaw: --")
        self.imu_label.setFont(font)
        self.imu_label.setAlignment(Qt.AlignCenter)

        self.distance_label = QLabel("Distance: --")
        self.distance_label.setFont(font)
        self.distance_label.setAlignment(Qt.AlignCenter)

        self.accel_label = QLabel("Accel X: --  Y: --  Z: --")
        self.accel_label.setFont(font)
        self.accel_label.setAlignment(Qt.AlignCenter)

        left_layout.addWidget(self.imu_label)
        left_layout.addWidget(self.distance_label)
        left_layout.addWidget(self.accel_label)

        zoom_label = QLabel("Zoom: 100%")
        zoom_slider = QSlider(Qt.Horizontal)
        zoom_slider.setMinimum(10)
        zoom_slider.setMaximum(200)
        zoom_slider.setValue(100)
        zoom_slider.setFixedWidth(250)
        zoom_slider.valueChanged.connect(lambda value: self.set_zoom_level(value, zoom_label))
        left_layout.addWidget(zoom_slider, alignment=Qt.AlignCenter)
        left_layout.addWidget(zoom_label, alignment=Qt.AlignCenter)

        # Back Button
        btn_back = QPushButton("Back")
        btn_back.setObjectName("btnNo")
        btn_back.setFont(QFont("Arial", 12))
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0)) 
        left_layout.addWidget(btn_back, alignment=Qt.AlignCenter)

                # Reconnect Button
        btn_reconnect = QPushButton("Reconnect")
        btn_reconnect.setObjectName("btnYes")
        btn_reconnect.clicked.connect(lambda: self.set_connection(SerialConnection(port=self.get_com_port(), baudrate=115200)))
        left_layout.addWidget(btn_reconnect, alignment=Qt.AlignCenter)

        # Reset Painter Button
        btn_reset = QPushButton("Reset View")
        btn_reset.setObjectName("btnYes")
        btn_reset.clicked.connect(self.reset_painter)
        left_layout.addWidget(btn_reset, alignment=Qt.AlignCenter)

        status_bar = QWidget()
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Disconnected")
        self.data_count_label = QLabel("Packets: 0")
        self.lost_count_label = QLabel("Lost: 0")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.data_count_label)
        status_layout.addWidget(self.lost_count_label)
        status_bar.setLayout(status_layout)
        left_layout.addWidget(status_bar, alignment=Qt.AlignCenter)

        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.view)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        self.apply_stylesheet("assets/stylesheets/base.qss")
        self.setLayout(layout)
    
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
                self.radar_data.append((data["pitch"], data["yaw"], data["distance"]))
                print(f"Added radar point: pitch={data["pitch"]}, yaw={data['yaw']}, distance={data['distance']}")  # Debug
                
        
            if len(self.imu_data) > 100:
               self.imu_data.pop(0)
            if len(self.radar_data) > 100:
                self.radar_data.pop(0)

            now = data.get("timestamp", 0)
            if self.last_timestamp is None:
                self.last_timestamp = now
                return
            dt = now - self.last_timestamp

                
            # Update position based on IMU (simplified)
            self.current_yaw = data["yaw"]
            movement_x = data.get("accel_x", 0) # Scale factor for visualization
            movement_y = data.get("accel_y", 0)
            
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
            
            def fmt(val):
                try:
                    return f"{float(val):.4f}"
                except (TypeError, ValueError):
                    return str(val) if val is not None else "--"

            self.imu_label.setText(
                f"Pitch: {fmt(data.get('pitch', '--'))}  Roll: {fmt(data.get('roll', '--'))}  Yaw: {fmt(data.get('yaw', '--'))}"
            )
            self.distance_label.setText(
                f"Distance: {fmt(data.get('distance', '--'))}"
            )
            self.accel_label.setText(
                f"Accel X: {fmt(data.get('accel_x', '--'))}  Y: {fmt(data.get('accel_y', '--'))}  Z: {fmt(data.get('accel_z', '--'))}"
            )
            
            self.update_display()
                
        except Exception as e:
            print(f"Error processing data: {e}")
    
    def update_display(self):
        """Update the minimap display"""
        
        # Draw radar walls (blue)
        wall_pen = QPen(QColor(0, 0, 255), 2)
        wall_brush = QBrush(QColor(0, 0, 255, 100))  # More opaque blue
        pitch= self.radar_data[-1][0]
        pitch_radians = -math.radians(pitch)
        yaw = self.radar_data[-1][1]
        distance = self.radar_data[-1][2]
        # Convert polar to cartesian coordinates (relative to person)
        yaw_radians = -math.radians(yaw)
        scaled_distance = distance / 2  # Scale down for better visibility
        x = self.current_position.x() + scaled_distance * math.cos(pitch_radians) * math.cos(yaw_radians)
        y = self.current_position.y() + scaled_distance * math.cos(pitch_radians) * math.sin(yaw_radians)
          
        # Draw wall point (larger size: 10x10 pixels)
        self.scene.addEllipse(x-5, y-5, 10, 10, wall_pen, wall_brush)
        
        matched = False
        for line in self.lines:
            if line.in_line_radius(x, y):
                matched = True
                line.add_point(x, y)
                

        if not matched:
            print("new line")
            new_line = IncrementalLinearRegression(start_point_x=x,start_point_y=y,scene=self.scene)
            new_line.add_point(x, y)
            self.lines.append(new_line)

        resolved_lines = []
        i =0
        while len(resolved_lines)<len(self.lines):
            j = i+1
            while j<len(self.lines):
                removed = self.lines[i].connect_lines(self.lines[j])
                if removed:
                    self.lines.pop(j)
                else:
                    j=j+1
            resolved_lines.append(self.lines[i])
            i+=1
        self.lines = resolved_lines

        # Draw person trail as green points
        trail_pen = QPen(QColor(0, 255, 0, 150), 2)
        trail_brush = QBrush(QColor(0, 255, 0, 150))
        for point in self.person_trail:
            self.scene.addEllipse(point.x() - 2, point.y() - 2, 4, 4, trail_pen, trail_brush)
        # Draw person (red circle with direction arrow)
        self.draw_person()
        
    def draw_person(self):
        """Draw the person with direction arrow, removing previous graphics"""
        # Remove previous person graphics if they exist
        if hasattr(self, 'person_graphics'):
            for item in self.person_graphics:
                self.scene.removeItem(item)
        
        # Store new graphics items
        self.person_graphics = []
        
        person_pen = QPen(Qt.red, 2)
        person_brush = QBrush(Qt.red)
        
        # Person circle
        person_radius = 3
        circle = self.scene.addEllipse(
            self.current_position.x() - person_radius, 
            self.current_position.y() - person_radius, 
            person_radius * 2, 
            person_radius * 2, 
            person_pen, 
            person_brush
        )
        self.person_graphics.append(circle)
        
        # Direction arrow
        arrow_length = 20
        rad = -math.radians(self.current_yaw)
        arrow_end = QPointF(
            self.current_position.x() + arrow_length * math.cos(rad),
            self.current_position.y() + arrow_length * math.sin(rad)
        )
        
        arrow_pen = QPen(Qt.red, 2)
        line = self.scene.addLine(
            self.current_position.x(), 
            self.current_position.y(), 
            arrow_end.x(), 
            arrow_end.y(), 
            arrow_pen
        )
        self.person_graphics.append(line)
        
        # Arrowhead
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
        head = self.scene.addPolygon(arrow_head, arrow_pen, QBrush(Qt.white))
        self.person_graphics.append(head)

    def reset_painter(self):
        self.scene.clear()
        self.lines.clear()
        self.person_trail.clear()
        self.person_graphics.clear()
        self.current_position = QPointF(0, 0)
        self.current_yaw = 0
   
    def set_zoom_level(self, value, label=None):
        scale_factor = value / 100.0
        if label:
            label.setText(f"Zoom: {value}%")
        self.view.resetTransform()
        self.view.scale(scale_factor, -scale_factor)







    def get_com_port(self):
        """Return the COM port number for the connected MCU, or None if not found."""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "USB" in port.description or "ACM" in port.device:
                return port.device
        if ports:
            return ports[0].device
        return None

    
    def apply_stylesheet(self, filename):
        try:
            with open(filename, "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Log: Stylesheet not found. Using default styles.")

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
