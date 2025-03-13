import numpy as np
import matplotlib.pyplot as plt
import json
import math
import argparse
import os
from matplotlib.patches import Polygon
import matplotlib.animation as animation

class SimulationDataProcessor:
    def __init__(self, json_file):
        """
        Initialize the processor with simulated sensor data.
        """
        self.json_file = json_file
        self.sensor_data = self._load_data()
        
        # Empty lists to store processed data
        self.positions = []
        self.headings = []
        self.radar_points = []
        
        # Create log directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
    
    def _load_data(self):
        """Load the simulated sensor data from the JSON file."""
        data = []
        with open(self.json_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    data.append(json.loads(line))
        return data
    
    def _reconstruct_room(self):
        """
        Attempt to reconstruct the room shape from radar data.
        This is a simplified implementation that tries to identify the vertices
        of the pentagonal room from the radar distance readings.
        """
        # Extract all radar endpoint coordinates
        all_radar_points = []
        for i, reading in enumerate(self.sensor_data):
            if i >= len(self.positions):  # Skip if position isn't calculated yet
                continue
                
            heading_rad = math.radians(reading['yaw'])
            distance = reading['distance'] / 100.0  # Convert from cm to meters
            
            x = self.positions[i][0] + distance * math.cos(heading_rad)
            y = self.positions[i][1] + distance * math.sin(heading_rad)
            
            all_radar_points.append((x, y))
        
        from scipy.spatial import ConvexHull
        
        if len(all_radar_points) < 5:  
            return None
            
        try:
            hull = ConvexHull(all_radar_points)
            hull_points = [all_radar_points[i] for i in hull.vertices]
            
            # If we have too many points, simplify
            if len(hull_points) > 5:
                # This is a naive simplification - in a real system,
                # you would use a more sophisticated algorithm
                step = len(hull_points) // 5
                simplified_hull = [hull_points[i] for i in range(0, len(hull_points), step)]
                while len(simplified_hull) > 5:
                    simplified_hull.pop()
                return simplified_hull
            
            return hull_points
        except:
            return None
    
    def _estimate_position(self, i, prev_x=0, prev_y=0):
        """
        Estimate position based on sensor reading.
        This is a dead reckoning approach that uses accelerometer data.
        """
        if i == 0:
            # Start at the origin for the first position
            return (0.0, 0.0)
        
        # Get time interval
        dt = (self.sensor_data[i]['timestamp'] - self.sensor_data[i-1]['timestamp']) / 1000.0  # Convert to seconds
        
        # Use accelerometer data to improve position estimate
        curr_reading = self.sensor_data[i-1]
        
        # If we have acceleration data available
        if 'accel_x' in curr_reading and 'accel_y' in curr_reading:
            # Convert accelerations from IMU frame to world frame
            heading_rad = math.radians(curr_reading['yaw'])
            
            # IMU acceleration is relative to the IMU heading
            # accel_x is lateral (left/right) in the IMU frame
            # accel_y is forward/backward in the IMU frame
            world_accel_x = (curr_reading['accel_y'] * math.cos(heading_rad) - 
                             curr_reading['accel_x'] * math.sin(heading_rad))
            world_accel_y = (curr_reading['accel_y'] * math.sin(heading_rad) + 
                             curr_reading['accel_x'] * math.cos(heading_rad))
            
            # Simple double integration for position (with damping)
            dx = world_accel_x * 0.5 * dt * dt
            dy = world_accel_y * 0.5 * dt * dt
            
            # Mix with basic dead reckoning for stability
            speed = 0.5  # meters per second
            dr_dx = speed * dt * math.cos(heading_rad)
            dr_dy = speed * dt * math.sin(heading_rad)
            
            # Weighted combination (mostly rely on dead reckoning for stability)
            dx = 0.2 * dx + 0.8 * dr_dx
            dy = 0.2 * dy + 0.8 * dr_dy
        else:
            # Fallback to simple dead reckoning
            heading_rad = math.radians(curr_reading['yaw'])
            speed = 0.5  # meters per second
            dx = speed * dt * math.cos(heading_rad)
            dy = speed * dt * math.sin(heading_rad)
        
        # Calculate new position
        new_x = prev_x + dx
        new_y = prev_y + dy
        
        return (new_x, new_y)
    
    def process_data(self):
        """Process the sensor data to reconstruct path and radar readings."""
        # Reset processed data
        self.positions = []
        self.headings = []
        self.radar_points = []
        
        # Process each sensor reading
        total_packets_lost = 0
        
        for i, reading in enumerate(self.sensor_data):
            # Check packets lost from the data (as if it was processed by the C code)
            if 'packets_lost' in reading:
                total_packets_lost = reading['packets_lost']
            
            # Get or estimate position
            if i == 0:
                pos = (0.0, 0.0)  # Start at origin
            else:
                pos = self._estimate_position(i, self.positions[-1][0], self.positions[-1][1])
            
            self.positions.append(pos)
            
            # Store heading
            heading = reading['yaw']
            self.headings.append(heading)
            
            # Calculate radar endpoint
            heading_rad = math.radians(heading)
            distance = reading['distance'] / 100.0  # Convert from cm to meters
            
            radar_x = pos[0] + distance * math.cos(heading_rad)
            radar_y = pos[1] + distance * math.sin(heading_rad)
            
            self.radar_points.append((radar_x, radar_y))
        
        # Attempt to reconstruct the room
        self.reconstructed_room = self._reconstruct_room()
        
        print(f"Processed {len(self.sensor_data)} sensor readings")
        print(f"Total packets lost according to sequence numbers: {total_packets_lost}")
    
    def plot_reconstruction(self, filename=None, show_animation=False):
        """Generate a visualization of the reconstructed path and room."""
        if not self.positions:
            print("No processed data available. Call process_data() first.")
            return
            
        if filename is None:
            # Generate default filename
            base_filename = os.path.basename(self.json_file)
            base_name = os.path.splitext(base_filename)[0]
            filename = f'logs/{base_name}_reconstruction.png'
        
        # Create subplots: main path plot and acceleration data plot
        fig = plt.figure(figsize=(15, 10))
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1])
        ax_path = fig.add_subplot(gs[0])
        ax_accel = fig.add_subplot(gs[1])
        
        # Path plot
        path_x = [pos[0] for pos in self.positions]
        path_y = [pos[1] for pos in self.positions]
        ax_path.plot(path_x, path_y, 'g-', linewidth=2, label='Reconstructed Path')
        
        ax_path.plot(path_x[0], path_y[0], 'go', markersize=8, label='Start')
        ax_path.plot(path_x[-1], path_y[-1], 'rx', markersize=8, label='End')
        
        # Plot the radar points
        radar_x = [point[0] for point in self.radar_points]
        radar_y = [point[1] for point in self.radar_points]
        ax_path.scatter(radar_x, radar_y, c='blue', s=10, alpha=0.5, label='Radar Points')
        
        # Plot radar lines for a subset of points
        step = max(1, len(self.positions) // 12)  # Show at most 12 points to avoid clutter
        
        for i in range(0, len(self.positions), step):
            x, y = self.positions[i]
            radar_x, radar_y = self.radar_points[i]
            
            # Plot position
            ax_path.plot(x, y, 'ro', markersize=6)
            
            heading_rad = math.radians(self.headings[i])
            dx = 0.5 * math.cos(heading_rad)
            dy = 0.5 * math.sin(heading_rad)
            ax_path.arrow(x, y, dx, dy, head_width=0.2, head_length=0.3, fc='red', ec='red')
            
            ax_path.plot([x, radar_x], [y, radar_y], 'r-', alpha=0.6)
        
        # Plot the reconstructed room if available
        if self.reconstructed_room:
            room = Polygon(self.reconstructed_room, fill=False, edgecolor='purple', 
                          linewidth=2, linestyle='--', label='Reconstructed Room')
            ax_path.add_patch(room)
        
        ax_path.legend()
        
        ax_path.set_xlabel('X (meters)')
        ax_path.set_ylabel('Y (meters)')
        ax_path.set_title('Reconstructed Path and Room')
        
        ax_path.set_aspect('equal')
        
        # Set limits automatically based on data
        min_x = min(min(pos[0] for pos in self.positions), min(point[0] for point in self.radar_points))
        max_x = max(max(pos[0] for pos in self.positions), max(point[0] for point in self.radar_points))
        min_y = min(min(pos[1] for pos in self.positions), min(point[1] for point in self.radar_points))
        max_y = max(max(pos[1] for pos in self.positions), max(point[1] for point in self.radar_points))
        
        padding = 2.0
        ax_path.set_xlim(min_x - padding, max_x + padding)
        ax_path.set_ylim(min_y - padding, max_y + padding)
        
        ax_path.grid(True, linestyle='--', alpha=0.7)
        
        # Acceleration plot
        timestamps = [reading['timestamp'] for reading in self.sensor_data]
        timestamps = [(t - timestamps[0])/1000.0 for t in timestamps]  # Convert to seconds from start
        
        if 'accel_x' in self.sensor_data[0]:
            accel_x = [reading['accel_x'] for reading in self.sensor_data]
            accel_y = [reading['accel_y'] for reading in self.sensor_data]
            accel_z = [reading['accel_z'] for reading in self.sensor_data]
            
            ax_accel.plot(timestamps, accel_x, 'r-', label='Accel X')
            ax_accel.plot(timestamps, accel_y, 'g-', label='Accel Y')
            ax_accel.plot(timestamps, accel_z, 'b-', label='Accel Z')
            
            ax_accel.set_xlabel('Time (seconds)')
            ax_accel.set_ylabel('Acceleration (m/s²)')
            ax_accel.set_title('IMU Acceleration Data')
            ax_accel.legend()
            ax_accel.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        
        if show_animation:
            self.create_animation()
        else:
            plt.close()
        
        print(f"Generated reconstruction visualization: {filename}")
        return filename
    
    def create_animation(self, filename=None):
        """Create an animation of the reconstructed path and radar readings."""
        if not self.positions:
            print("No processed data available. Call process_data() first.")
            return
            
        if filename is None:
            # Generate default filename
            base_filename = os.path.basename(self.json_file)
            base_name = os.path.splitext(base_filename)[0]
            filename = f'logs/{base_name}_animation.gif'  
        
        # Create figure with subplots - main plot and acceleration subplot
        fig = plt.figure(figsize=(15, 10))
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1])
        ax_path = fig.add_subplot(gs[0])
        ax_accel = fig.add_subplot(gs[1])
        
        # Path plot elements
        path_line, = ax_path.plot([], [], 'g-', linewidth=2)
        position_marker, = ax_path.plot([], [], 'ro', markersize=8)
        radar_line, = ax_path.plot([], [], 'r-', alpha=0.8)
        radar_points = ax_path.scatter([], [], c='blue', s=10, alpha=0.5)
        
        # Plot the reconstructed room if available
        if self.reconstructed_room:
            room = Polygon(self.reconstructed_room, fill=False, edgecolor='purple', 
                          linewidth=2, linestyle='--')
            ax_path.add_patch(room)
        
        ax_path.set_xlabel('X (meters)')
        ax_path.set_ylabel('Y (meters)')
        ax_path.set_title('Simulated Path and Radar Readings')
        
        ax_path.set_aspect('equal')
        
        min_x = min(min(pos[0] for pos in self.positions), min(point[0] for point in self.radar_points))
        max_x = max(max(pos[0] for pos in self.positions), max(point[0] for point in self.radar_points))
        min_y = min(min(pos[1] for pos in self.positions), min(point[1] for point in self.radar_points))
        max_y = max(max(pos[1] for pos in self.positions), max(point[1] for point in self.radar_points))
        
        padding = 2.0
        ax_path.set_xlim(min_x - padding, max_x + padding)
        ax_path.set_ylim(min_y - padding, max_y + padding)
        
        ax_path.grid(True, linestyle='--', alpha=0.7)
        
        # Setup for acceleration plot
        has_accel_data = 'accel_x' in self.sensor_data[0]
        timestamps = [reading['timestamp'] for reading in self.sensor_data]
        timestamps = [(t - timestamps[0])/1000.0 for t in timestamps]  # Convert to seconds from start
        
        if has_accel_data:
            accel_x = [reading['accel_x'] for reading in self.sensor_data]
            accel_y = [reading['accel_y'] for reading in self.sensor_data]
            accel_z = [reading['accel_z'] for reading in self.sensor_data]
            
            accel_x_line, = ax_accel.plot([], [], 'r-', label='Accel X')
            accel_y_line, = ax_accel.plot([], [], 'g-', label='Accel Y')
            accel_z_line, = ax_accel.plot([], [], 'b-', label='Accel Z')
            current_time_marker = ax_accel.axvline(x=0, color='k', linestyle='--')
            
            ax_accel.set_xlabel('Time (seconds)')
            ax_accel.set_ylabel('Acceleration (m/s²)')
            ax_accel.set_title('IMU Acceleration Data')
            
            # Set y limits for acceleration
            ax_accel.set_xlim(0, timestamps[-1])
            max_accel = max(max(abs(a) for a in accel_x), max(abs(a) for a in accel_y), max(abs(a) for a in accel_z))
            ax_accel.set_ylim(-max_accel * 1.1, max_accel * 1.1)
            
            ax_accel.legend()
            ax_accel.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        def init():
            path_line.set_data([], [])
            position_marker.set_data([], [])
            radar_line.set_data([], [])
            radar_points.set_offsets(np.empty((0, 2)))
            
            if has_accel_data:
                accel_x_line.set_data([], [])
                accel_y_line.set_data([], [])
                accel_z_line.set_data([], [])
                current_time_marker.set_xdata([0])
                return path_line, position_marker, radar_line, radar_points, accel_x_line, accel_y_line, accel_z_line, current_time_marker
            
            return path_line, position_marker, radar_line, radar_points
        
        def animate(i):
            # Plot the path up to the current frame
            path_x = [pos[0] for pos in self.positions[:i+1]]
            path_y = [pos[1] for pos in self.positions[:i+1]]
            path_line.set_data(path_x, path_y)
            
            # Plot the current position
            position_marker.set_data([self.positions[i][0]], [self.positions[i][1]])
            
            # Plot the radar line for the current position
            radar_line.set_data(
                [self.positions[i][0], self.radar_points[i][0]], 
                [self.positions[i][1], self.radar_points[i][1]]
            )
            
            # Plot all radar points up to the current frame
            radar_data = np.array(self.radar_points[:i+1])
            radar_points.set_offsets(radar_data)
            
            # Update acceleration plot
            if has_accel_data:
                accel_x_line.set_data(timestamps[:i+1], accel_x[:i+1])
                accel_y_line.set_data(timestamps[:i+1], accel_y[:i+1])
                accel_z_line.set_data(timestamps[:i+1], accel_z[:i+1])
                current_time_marker.set_xdata([timestamps[i]])
                return path_line, position_marker, radar_line, radar_points, accel_x_line, accel_y_line, accel_z_line, current_time_marker
            
            return path_line, position_marker, radar_line, radar_points
        
        # Create the animation
        num_frames = len(self.positions)
        ani = animation.FuncAnimation(
            fig, animate, frames=num_frames, init_func=init, blit=True, interval=50
        )
        
        try:
            # Try to save with ffmpeg first (for MP4)
            writer = 'ffmpeg' if animation.writers.is_available('ffmpeg') else 'pillow'
            
            if writer == 'ffmpeg' and not filename.endswith('.gif'):
                # If ffmpeg is available and filename is not a GIF, use MP4
                if not filename.endswith('.mp4'):
                    filename = filename.rsplit('.', 1)[0] + '.mp4'
                
                print(f"Using ffmpeg to create MP4 animation: {filename}")
                ani.save(filename, writer='ffmpeg', fps=15, dpi=200)
            else:
                # Use pillow for GIF format (should be widely compatible ??)
                if not filename.endswith('.gif'):
                    filename = filename.rsplit('.', 1)[0] + '.gif'
                
                print(f"Using pillow to create GIF animation: {filename}")
                ani.save(filename, writer='pillow', fps=10, dpi=100)
        except Exception as e:
            print(f"Error saving animation: {e}")
        
        plt.close()
        return filename

def main():
    parser = argparse.ArgumentParser(description='Process simulated sensor data')
    parser.add_argument('--input', required=True, help='Input JSON file with simulated data')
    parser.add_argument('--output', help='Output plot filename')
    parser.add_argument('--animate', action='store_true', help='Create an animation')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return
    
    print(f"Processing simulated data from: {args.input}")
    processor = SimulationDataProcessor(args.input)
    processor.process_data()
    output_file = processor.plot_reconstruction(args.output, args.animate)
    
    print("Processing completed successfully!")
    print(f"Generated visualization: {output_file}")
    
    if args.animate:
        print("Animation generated in the same directory.")

if __name__ == "__main__":
    main()
