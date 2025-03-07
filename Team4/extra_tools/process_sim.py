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
        This is a simple dead reckoning approach.
        """
        if i == 0:
            # Start at the origin for the first position
            return (0.0, 0.0)
        
        # Get time interval
        dt = (self.sensor_data[i]['timestamp'] - self.sensor_data[i-1]['timestamp']) / 1000.0  # Convert to seconds
        
        # Assume a constant movement speed (adjust as needed)
        speed = 0.5  # meters per second
        
        # Calculate displacement based on heading
        heading_rad = math.radians(self.sensor_data[i-1]['yaw'])
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
        for i, reading in enumerate(self.sensor_data):
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
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        path_x = [pos[0] for pos in self.positions]
        path_y = [pos[1] for pos in self.positions]
        ax.plot(path_x, path_y, 'g-', linewidth=2, label='Reconstructed Path')
        
        ax.plot(path_x[0], path_y[0], 'go', markersize=8, label='Start')
        ax.plot(path_x[-1], path_y[-1], 'rx', markersize=8, label='End')
        
        # Plot the radar points
        radar_x = [point[0] for point in self.radar_points]
        radar_y = [point[1] for point in self.radar_points]
        ax.scatter(radar_x, radar_y, c='blue', s=10, alpha=0.5, label='Radar Points')
        
        # Plot radar lines for a subset of points
        step = max(1, len(self.positions) // 12)  # Show at most 12 points to avoid clutter
        
        for i in range(0, len(self.positions), step):
            x, y = self.positions[i]
            radar_x, radar_y = self.radar_points[i]
            
            # Plot position
            ax.plot(x, y, 'ro', markersize=6)
            
            heading_rad = math.radians(self.headings[i])
            dx = 0.5 * math.cos(heading_rad)
            dy = 0.5 * math.sin(heading_rad)
            ax.arrow(x, y, dx, dy, head_width=0.2, head_length=0.3, fc='red', ec='red')
            
            ax.plot([x, radar_x], [y, radar_y], 'r-', alpha=0.6)
        
        # Plot the reconstructed room if available
        if self.reconstructed_room:
            room = Polygon(self.reconstructed_room, fill=False, edgecolor='purple', 
                          linewidth=2, linestyle='--', label='Reconstructed Room')
            ax.add_patch(room)
        
        ax.legend()
        
        ax.set_xlabel('X (meters)')
        ax.set_ylabel('Y (meters)')
        ax.set_title('Reconstructed Path and Room')
        
        ax.set_aspect('equal')
        
        # Set limits automatically based on data
        min_x = min(min(pos[0] for pos in self.positions), min(point[0] for point in self.radar_points))
        max_x = max(max(pos[0] for pos in self.positions), max(point[0] for point in self.radar_points))
        min_y = min(min(pos[1] for pos in self.positions), min(point[1] for point in self.radar_points))
        max_y = max(max(pos[1] for pos in self.positions), max(point[1] for point in self.radar_points))
        
        padding = 2.0
        ax.set_xlim(min_x - padding, max_x + padding)
        ax.set_ylim(min_y - padding, max_y + padding)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        
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
        
        fig, ax = plt.subplots(figsize=(10, 10))
        
        path_line, = ax.plot([], [], 'g-', linewidth=2)
        position_marker, = ax.plot([], [], 'ro', markersize=8)
        radar_line, = ax.plot([], [], 'r-', alpha=0.8)
        radar_points = ax.scatter([], [], c='blue', s=10, alpha=0.5)
        
        # Plot the reconstructed room if available
        if self.reconstructed_room:
            room = Polygon(self.reconstructed_room, fill=False, edgecolor='purple', 
                          linewidth=2, linestyle='--')
            ax.add_patch(room)
        
        ax.set_xlabel('X (meters)')
        ax.set_ylabel('Y (meters)')
        ax.set_title('Simulated Path and Radar Readings')
        
        ax.set_aspect('equal')
        
        min_x = min(min(pos[0] for pos in self.positions), min(point[0] for point in self.radar_points))
        max_x = max(max(pos[0] for pos in self.positions), max(point[0] for point in self.radar_points))
        min_y = min(min(pos[1] for pos in self.positions), min(point[1] for point in self.radar_points))
        max_y = max(max(pos[1] for pos in self.positions), max(point[1] for point in self.radar_points))
        
        padding = 2.0
        ax.set_xlim(min_x - padding, max_x + padding)
        ax.set_ylim(min_y - padding, max_y + padding)
        
        ax.grid(True, linestyle='--', alpha=0.7)
        
        def init():
            path_line.set_data([], [])
            position_marker.set_data([], [])
            radar_line.set_data([], [])
            radar_points.set_offsets(np.empty((0, 2)))
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
