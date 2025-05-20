import sys
import json
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                            QGraphicsScene, QVBoxLayout, QWidget, QLabel, 
                            QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, QPointF, QObject, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF, QColor

#For ease of implementation a line wiil be initiliased with a single point
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
            self.update_end_points(x,y)
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
            print("out")
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
        
    def update_end_points(self, x, y):
        if (self.in_boundary(x,y))==False:
            (x0, y0), (x1, y1) = self.end_points

            if (self.slope ** 2) < 1:
                new_y = self.predict(x)
                new_point = (self.predict_x(new_y), new_y)

                if x < min(x0, x1):
                    index = 0 if x0 < x1 else 1
                    self.end_points[index] = new_point
                elif x > max(x0, x1):
                    index = 0 if x0 > x1 else 1
                    self.end_points[index] = new_point
            else:
                new_x = self.predict_x(y)
                new_point = (new_x, self.predict(new_x))

                if y < min(y0, y1):
                    index = 0 if y0 < y1 else 1
                    self.end_points[index] = new_point
                elif y > max(y0, y1):
                    index = 0 if y0 > y1 else 1
                    self.end_points[index] = new_point

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
        self.person_graphics = []
        self.prev_point = None

        # Connection
        self.connection = None

        self.lines = []
        
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
            
            self.update_display()
                
        except Exception as e:
            print(f"Error processing data: {e}")
    
    def update_display(self):
        """Update the minimap display"""
        
        # Draw radar walls (blue)
        wall_pen = QPen(QColor(0, 0, 255), 2)
        wall_brush = QBrush(QColor(0, 0, 255, 100))  # More opaque blue
        
        yaw = self.radar_data[-1][0]
        distance = self.radar_data[-1][1]
        # Convert polar to cartesian coordinates (relative to person)
        rad = -math.radians(yaw)
        scaled_distance = distance / 2  # Scale down for better visibility
        x = self.current_position.x() + scaled_distance * math.cos(rad)
        y = self.current_position.y() + scaled_distance * math.sin(rad)
          
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

        # Draw person trail (green)
        if len(self.person_trail) > 1:
            trail_pen = QPen(QColor(0, 255, 0, 150), 2)
            path = QPolygonF(self.person_trail)
            self.scene.addPolygon(path, trail_pen)
        
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
    window.set_connection(SerialConnection(port='COM3', baudrate=115200))
    
    window.show()
    sys.exit(app.exec_())