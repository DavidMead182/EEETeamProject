import numpy as np
import matplotlib.pyplot as plt
import json
import math
import time
import datetime
import argparse
import os
from matplotlib.patches import Polygon

class PentagonalRoomSimulator:
    def __init__(self, room_size=10.0, circle_radius=3.0, num_steps=120, noise_level=0.2):
        """
        Initialize the simulator for a pentagonal room with a circular path.
        
        room_size: Size of the pentagonal room (distance from center to vertices)
        num_steps: Number of steps to take in the simulation
        """
        self.room_size = room_size
        self.circle_radius = circle_radius
        self.num_steps = num_steps
        self.noise_level = noise_level
        
        # Generate the pentagonal room vertices
        self.room_vertices = self._generate_pentagon(room_size)
        
        os.makedirs('logs', exist_ok=True)
        
        self.positions, self.headings = self._generate_circle_path(circle_radius, num_steps)
        
        self.radar_readings = self._compute_radar_distances()
        
        # Convert to sensor readings (with noise)
        self.sensor_readings = self._generate_sensor_readings()
    
    def _generate_pentagon(self, size):
        """Generate vertices of a regular pentagon centered at the origin."""
        vertices = []
        for i in range(5):
            angle = 2 * math.pi * i / 5 + math.pi/10  # Rotate slightly to look better
            x = size * math.cos(angle)
            y = size * math.sin(angle)
            vertices.append((x, y))
        return vertices
    
    def _generate_circle_path(self, radius, num_steps):
        """Generate positions and headings along a circular path."""
        positions = []
        headings = []
        
        for i in range(num_steps):
            angle = 2 * math.pi * i / num_steps
            
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            positions.append((x, y))
            
            heading_angle = angle + math.pi/2
            heading_angle = heading_angle % (2 * math.pi)  
            heading_degrees = math.degrees(heading_angle) % 360  
            headings.append(heading_degrees)
        
        return positions, headings
    
    def _intersect_ray_segment(self, ray_origin, ray_dir, segment_start, segment_end):
        """
        Calculate the intersection of a ray with a line segment.
        
        ray_origin: Origin point of the ray (x, y)
        ray_dir: Direction of the ray (angle in radians)
        segment_start: Start point of the segment (x, y)
        segment_end: End point of the segment (x, y)
        """
        # Convert ray direction to a vector
        ray_dir_x = math.cos(ray_dir)
        ray_dir_y = math.sin(ray_dir)
        
        # Calculate segment direction
        segment_dir_x = segment_end[0] - segment_start[0]
        segment_dir_y = segment_end[1] - segment_start[1]
        
        # Calculate determinant to check if ray and segment are parallel
        det = segment_dir_x * (-ray_dir_y) - segment_dir_y * (-ray_dir_x)
        
        if abs(det) < 1e-6:  # Parallel
            return None
        
        # Calculate parameter values
        t = ((ray_origin[0] - segment_start[0]) * (-ray_dir_y) - 
             (ray_origin[1] - segment_start[1]) * (-ray_dir_x)) / det
        
        u = ((segment_start[0] - ray_origin[0]) * (-segment_dir_y) - 
             (segment_start[1] - ray_origin[1]) * (-segment_dir_x)) / (-det)
        
        # Check if intersection is within segment and in front of ray
        if 0 <= t <= 1 and u >= 0:
            # Calculate intersection point
            intersection_x = segment_start[0] + t * segment_dir_x
            intersection_y = segment_start[1] + t * segment_dir_y
            
            # Calculate distance from ray origin to intersection
            distance = math.sqrt((intersection_x - ray_origin[0])**2 + 
                               (intersection_y - ray_origin[1])**2)
            
            return distance
        
        return None
    
    def _compute_radar_distance(self, position, heading_degrees):
        """Compute the radar distance reading for a given position and heading."""
        heading_rad = math.radians(heading_degrees)
        
        distances = []
        
        for i in range(5):
            wall_start = self.room_vertices[i]
            wall_end = self.room_vertices[(i + 1) % 5]
            
            distance = self._intersect_ray_segment(position, heading_rad, wall_start, wall_end)
            if distance is not None:
                distances.append(distance)
        
        if distances:
            return min(distances)  # Return the closest wall distance
        else:
            return 100.0  
    
    def _compute_radar_distances(self):
        """Compute radar distances for all positions and headings."""
        radar_readings = []
        
        for i in range(self.num_steps):
            distance = self._compute_radar_distance(self.positions[i], self.headings[i])
            radar_readings.append(distance)
        
        return radar_readings
    
    def _add_noise(self, value, noise_scale):
        """Add random noise to a value."""
        noise = np.random.normal(0, noise_scale)
        return value + noise
    
    def _generate_sensor_readings(self):
        """Generate simulated sensor readings with noise."""
        readings = []
        
        pitch_drift = 0.0
        roll_drift = 0.0
        sequence = 0
        
        for i in range(self.num_steps):
            timestamp = int(time.time() * 1000) + i * 100  # Milliseconds with 100 millisecond intervals
            
            # Add random drift to pitch and roll
            pitch_drift += np.random.normal(0, 0.1)
            roll_drift += np.random.normal(0, 0.1)
            pitch_drift = max(-10, min(10, pitch_drift))
            roll_drift = max(-10, min(10, roll_drift))
            
            # Generate simulated accelerometer readings based on orientation
            # These are simplified and don't account for proper physics
            heading_rad = math.radians(self.headings[i])
            # Simulate acceleration relative to IMU heading
            accel_x = self._add_noise(0.0, self.noise_level * 0.5)  # Lateral acceleration
            accel_y = self._add_noise(0.0, self.noise_level * 0.5)  # Forward/backward acceleration
            accel_z = self._add_noise(9.81, self.noise_level)  # Vertical (gravity) acceleration
            
            # Get values to generate the string format
            pitch = self._add_noise(pitch_drift, self.noise_level * 2)
            roll = self._add_noise(roll_drift, self.noise_level * 2)
            yaw = self._add_noise(self.headings[i], self.noise_level * 5)
            distance = self._add_noise(self.radar_readings[i] * 100, self.noise_level * 10)  # Convert to cm
            
            # Format using the string format expected by the C code parser
            # Format sequence as 3-digit hex
            raw_data = f"SEQ:{sequence:03x},P:{pitch:.2f},R:{roll:.2f},Y:{yaw:.2f},D:{distance:.2f},"
            raw_data += f"AX:{accel_x:.2f},AY:{accel_y:.2f},AZ:{accel_z:.2f},T:{timestamp}"
            
            # Create the JSON as it would be after C code parsing
            reading = {
                "sequence": sequence,
                "packets_lost": 0,  # Will be calculated by the C code in real device
                "pitch": pitch,
                "roll": roll,
                "yaw": yaw,
                "distance": distance,
                "accel_x": accel_x,
                "accel_y": accel_y,
                "accel_z": accel_z,
                "timestamp": timestamp
            }
            
            # Store raw data separately for generating the raw format file
            self.raw_data_strings = getattr(self, 'raw_data_strings', [])
            self.raw_data_strings.append(raw_data)
            
            readings.append(reading)
            
            # Increment sequence number and wrap at 4095 (0xFFF)
            sequence = (sequence + 1) % 4096
        
        return readings
    
    def generate_json(self, filename=None):
        """Generate and save sensor readings as JSON."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/simulated_data_{timestamp}.json'
        
        with open(filename, 'w') as f:
            for reading in self.sensor_readings:
                f.write(json.dumps(reading) + '\n')
        
        # Also generate raw data format (just the string representation)
        raw_filename = filename.replace('.json', '_raw.txt')
        with open(raw_filename, 'w') as f:
            for raw_data in self.raw_data_strings:
                f.write(raw_data + '\n')
        
        print(f"Generated simulated data: {filename}")
        print(f"Generated raw format data: {raw_filename}")
        return filename
    
    def plot_visualization(self, filename=None):
        """Create a visualization of the room, path, and radar readings."""
        if filename is None:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logs/simulation_plot_{timestamp}.png'
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        room = Polygon(self.room_vertices, fill=False, edgecolor='blue', linewidth=2)
        ax.add_patch(room)
        
        path_x = [pos[0] for pos in self.positions]
        path_y = [pos[1] for pos in self.positions]
        ax.plot(path_x, path_y, 'g-', linewidth=1, alpha=0.5)
        
        # Plot the positions and radar lines for a subset of points
        step = max(1, self.num_steps // 12)  # Show at most 12 points to avoid clutter
        
        for i in range(0, self.num_steps, step):
            x, y = self.positions[i]
            heading_rad = math.radians(self.headings[i])
            distance = self.radar_readings[i]
            
            # Plot position
            ax.plot(x, y, 'ro', markersize=6)
            
            # Plot direction
            dx = 0.5 * math.cos(heading_rad)
            dy = 0.5 * math.sin(heading_rad)
            ax.arrow(x, y, dx, dy, head_width=0.2, head_length=0.3, fc='red', ec='red')
            
            # Plot radar line to wall
            radar_x = x + distance * math.cos(heading_rad)
            radar_y = y + distance * math.sin(heading_rad)
            ax.plot([x, radar_x], [y, radar_y], 'r-', alpha=0.6)
        
        # Add a legend and labels
        ax.plot([], [], 'g-', label='Path')
        ax.plot([], [], 'ro', label='Position')
        ax.plot([], [], 'r-', label='Radar Reading')
        ax.legend()
        
        ax.set_xlabel('X (meters)')
        ax.set_ylabel('Y (meters)')
        ax.set_title('Simulated Path in Pentagonal Room')
        
        ax.set_aspect('equal')
        
        padding = 1.5
        ax.set_xlim(-self.room_size - padding, self.room_size + padding)
        ax.set_ylim(-self.room_size - padding, self.room_size + padding)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Generated visualization: {filename}")
        return filename
    
    def run_simulation(self):
        """Run the full simulation, generating data and visualization."""
        json_file = self.generate_json()
        plot_file = self.plot_visualization()
        return json_file, plot_file

def main():
    parser = argparse.ArgumentParser(description='Simulate sensor data for walking in a pentagonal room')
    parser.add_argument('--room-size', type=float, default=10.0, help='Size of the pentagonal room (meters)')
    parser.add_argument('--path-radius', type=float, default=3.0, help='Radius of the circular path (meters)')
    parser.add_argument('--steps', type=int, default=120, help='Number of steps in the simulation')
    parser.add_argument('--noise', type=float, default=0.2, help='Noise level (0-1)')
    parser.add_argument('--output-json', help='Output JSON filename')
    parser.add_argument('--output-plot', help='Output plot filename')
    
    args = parser.parse_args()
    
    simulator = PentagonalRoomSimulator(
        room_size=args.room_size,
        circle_radius=args.path_radius,
        num_steps=args.steps,
        noise_level=args.noise
    )
    
    json_file = simulator.generate_json(args.output_json)
    plot_file = simulator.plot_visualization(args.output_plot)
    
    print("Simulation completed successfully!")
    print(f"Generated JSON data: {json_file}")
    print(f"Generated visualization: {plot_file}")
    print("\nTo process this data, run:")
    print(f"python process_sim.py --input {json_file}")

if __name__ == "__main__":
    main()
