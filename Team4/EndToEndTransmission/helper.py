import serial
import serial.tools.list_ports
import json
import time
import datetime
import math
import argparse
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.dates as mdates
from collections import deque
import threading

class SensorDataProcessor:
    def __init__(self, com_port, baud_rate=9600):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.raw_log_file = None
        self.processed_log_file = None
        
        # Create log directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create log files with timestamp in the name
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.raw_log_filename = f'logs/raw_data_{timestamp}.json'
        self.processed_log_filename = f'logs/processed_data_{timestamp}.txt'
        
        self.raw_log_file = open(self.raw_log_filename, 'w')
        self.processed_log_file = open(self.processed_log_filename, 'w')
        
        print(f"Logging raw data to: {self.raw_log_filename}")
        print(f"Logging processed data to: {self.processed_log_filename}")
        
        # Data for live plotting
        self.plot_lock = threading.Lock()
        self.time_data = deque(maxlen=100)
        self.packets_received = deque(maxlen=100)
        self.packets_lost = deque(maxlen=100)
        self.loss_percentage = deque(maxlen=100)
        self.total_packets_received = 0
        self.total_packets_lost = 0
        self.plot_active = False
    
    def connect(self):
        """Connect to the Arduino via serial port"""
        try:
            self.serial_conn = serial.Serial(self.com_port, self.baud_rate, timeout=1)
            print(f"Connected to {self.com_port} at {self.baud_rate} baud")
            return True
        except serial.SerialException as e:
            print(f"Error connecting to serial port {self.com_port}: {e}")
            return False
    
    def close(self):
        """Close serial connection and log files"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("Serial connection closed")
        
        if self.raw_log_file:
            self.raw_log_file.close()
            print(f"Raw log file closed: {self.raw_log_filename}")
        
        if self.processed_log_file:
            self.processed_log_file.close()
            print(f"Processed log file closed: {self.processed_log_filename}")
            
        # Stop the plotting
        self.plot_active = False
    
    def process_data(self, json_data):
        """Process the sensor data and extract useful information"""
        try:
            # Parse the JSON data
            data = json.loads(json_data)
            
            # Get current time for the log
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            timestamp = datetime.datetime.now()
            
            # Calculate cardinal direction from yaw
            cardinal_direction = self._get_cardinal_direction(data.get('yaw', 0))
            
            # Get packet sequence and loss information
            sequence = data.get('sequence', 0)
            packets_lost = data.get('packets_lost', 0)
            
            # Update plot data
            with self.plot_lock:
                self.total_packets_received += 1
                self.total_packets_lost = packets_lost
                
                # Calculate loss percentage
                if self.total_packets_received + self.total_packets_lost > 0:
                    loss_percent = (self.total_packets_lost / (self.total_packets_received + self.total_packets_lost)) * 100
                else:
                    loss_percent = 0
                
                self.time_data.append(timestamp)
                self.packets_received.append(self.total_packets_received)
                self.packets_lost.append(self.total_packets_lost)
                self.loss_percentage.append(loss_percent)
            
            # Create a processed data record
            processed_data = {
                "time": current_time,
                "arduino_time_ms": data.get('timestamp', 0),
                "packet": {
                    "sequence": sequence,
                    "packets_lost": packets_lost,
                    "loss_percentage": loss_percent
                },
                "orientation": {
                    "pitch": data.get('pitch', 0),
                    "roll": data.get('roll', 0),
                    "yaw": data.get('yaw', 0),
                    "cardinal_direction": cardinal_direction
                },
                "acceleration": {
                    "x": data.get('accel_x', 0),
                    "y": data.get('accel_y', 0),
                    "z": data.get('accel_z', 0)
                },
                "radar": {
                    "distance_cm": data.get('distance', 0),
                    "direction": cardinal_direction
                }
            }
            
            # Create a human-readable summary with packet loss percentage
            loss_percentage_str = f"{loss_percent:.2f}%"
            summary = (
                f"Time: {current_time}\n"
                f"Packet: Seq={sequence} (Lost: {packets_lost}, Loss Rate: {loss_percentage_str})\n"
                f"Orientation: Pitch={data.get('pitch', 0):.2f}°, "
                f"Roll={data.get('roll', 0):.2f}°, "
                f"Yaw={data.get('yaw', 0):.2f}° ({cardinal_direction})\n"
                f"Acceleration: X={data.get('accel_x', 0):.2f}, "
                f"Y={data.get('accel_y', 0):.2f}, "
                f"Z={data.get('accel_z', 0):.2f} m/s²\n"
                f"Radar: {data.get('distance', 0):.2f} cm @ {cardinal_direction}\n"
                f"-------------------------\n"
            )
            
            return processed_data, summary
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            print(f"Problematic data: {json_data}")
            return None, None
    
    def _get_cardinal_direction(self, yaw):
        """Convert yaw angle to cardinal direction"""
        # Ensure yaw is within 0-360 range
        yaw = yaw % 360
        
        # Define cardinal directions with their degree ranges
        directions = [
            ("N", (337.5, 360), (0, 22.5)),
            ("NE", (22.5, 67.5)),
            ("E", (67.5, 112.5)),
            ("SE", (112.5, 157.5)),
            ("S", (157.5, 202.5)),
            ("SW", (202.5, 247.5)),
            ("W", (247.5, 292.5)),
            ("NW", (292.5, 337.5))
        ]
        
        # Special case for North (spans 337.5-360 and 0-22.5)
        if yaw >= 337.5 or yaw < 22.5:
            return "N"
        
        # Check other directions
        for direction, *ranges in directions:
            for range_tuple in ranges:
                if len(range_tuple) == 2 and range_tuple[0] <= yaw < range_tuple[1]:
                    return direction
        
        # Default in case of an error
        return "Unknown"
    
    def initialize_plot(self):
        """Initialize the matplotlib plot for packet loss visualization"""
        # Use non-interactive backend if running headless
        try:
            plt.ion()  # Enable interactive mode
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
            self.ax.set_title('Packet Loss Percentage')
            self.ax.set_xlabel('Time')
            self.ax.set_ylabel('Loss Percentage (%)')
            self.ax.grid(True)
            
            # Setup time formatting for x-axis
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            self.ax.xaxis.set_tick_params(rotation=45)
            
            # Use dummy time values initially (convert to matplotlib date numbers)
            now = datetime.datetime.now()
            initial_times = [mdates.date2num(now)]
            initial_values = [0]
            self.loss_line, = self.ax.plot(initial_times, initial_values, 'r-', label='Packet Loss %')
            
            self.ax.legend()
            self.ax.set_ylim(0, 100)  # Loss percentage range
            plt.tight_layout()
            
            # Add initial info text
            self.info_text = self.ax.text(0.02, 0.95, 
                                         f'Current Loss: 0.00%\n'
                                         f'Total Packets: 0\n'
                                         f'Lost Packets: 0',
                                         transform=self.ax.transAxes,
                                         fontsize=10, verticalalignment='top',
                                         bbox=dict(facecolor='white', alpha=0.5))
            
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            print("Plot initialized successfully")
        except Exception as e:
            print(f"Error initializing plot: {e}")
            self.plot_active = False
    
    def update_plot(self, frame):
        """Update function for the animation"""
        if not self.plot_active:
            return
        
        try:
            with self.plot_lock:
                if len(self.time_data) > 0:
                    # Convert datetime objects to matplotlib dates
                    times = [mdates.date2num(t) for t in self.time_data]
                    loss_pcts = list(self.loss_percentage)
                    
                    # Update the line data
                    self.loss_line.set_xdata(times)
                    self.loss_line.set_ydata(loss_pcts)
                    
                    # Adjust x-axis to show the most recent data
                    self.ax.set_xlim(times[0], times[-1])
                    self.fig.autofmt_xdate()  # Auto-format the x date labels
                    
                    # If we have significant loss, adjust y-axis
                    if loss_pcts and max(loss_pcts) > 0:
                        max_loss = max(loss_pcts)
                        y_max = min(100, max(10, max_loss * 1.2))  # Set reasonable upper limit
                        self.ax.set_ylim(0, y_max)
                    
                    # Update info text
                    if hasattr(self, 'info_text') and self.info_text:
                        self.info_text.remove()
                        
                    latest_loss = loss_pcts[-1] if loss_pcts else 0
                    total_received = self.total_packets_received
                    total_lost = self.total_packets_lost
                    
                    self.info_text = self.ax.text(0.02, 0.95, 
                                                f'Current Loss: {latest_loss:.2f}%\n'
                                                f'Total Packets: {total_received}\n'
                                                f'Lost Packets: {total_lost}',
                                                transform=self.ax.transAxes,
                                                fontsize=10, verticalalignment='top',
                                                bbox=dict(facecolor='white', alpha=0.5))
                    
                    # Redraw the plot
                    self.fig.canvas.draw()
                    self.fig.canvas.flush_events()
                    
        except Exception as e:
            print(f"Error updating plot: {e}")
            self.plot_active = False
    
    def start_plotting(self):
        """Start the plotting in a background thread"""
        try:
            self.plot_active = True
            
            # Use a simpler plotting approach as a backup option
            # Initialize simple plot
            plt.figure(figsize=(10, 6))
            plt.title('Packet Loss Percentage')
            plt.xlabel('Sample')
            plt.ylabel('Loss Percentage (%)')
            plt.ylim(0, 100)
            plt.grid(True)
            
            # Create a background thread to update the plot periodically
            def update_thread():
                count = 0
                while self.plot_active:
                    try:
                        with self.plot_lock:
                            loss_pcts = list(self.loss_percentage)
                            if loss_pcts:
                                plt.clf()
                                plt.title('Packet Loss Percentage')
                                plt.xlabel('Sample')
                                plt.ylabel('Loss Percentage (%)')
                                
                                # Use sample numbers for x-axis instead of times
                                sample_nums = list(range(len(loss_pcts)))
                                
                                plt.plot(sample_nums, loss_pcts, 'r-', label='Packet Loss %')
                                
                                # Set y-limits based on data
                                if max(loss_pcts) > 0:
                                    y_max = min(100, max(10, max(loss_pcts) * 1.2))
                                    plt.ylim(0, y_max)
                                else:
                                    plt.ylim(0, 10)
                                
                                # Add text annotation
                                latest_loss = loss_pcts[-1] if loss_pcts else 0
                                plt.annotate(f'Current Loss: {latest_loss:.2f}%\n'
                                             f'Total Packets: {self.total_packets_received}\n'
                                             f'Lost Packets: {self.total_packets_lost}',
                                             xy=(0.02, 0.95), xycoords='axes fraction',
                                             fontsize=10, verticalalignment='top',
                                             bbox=dict(facecolor='white', alpha=0.5))
                                
                                plt.grid(True)
                                plt.legend()
                                plt.draw()
                                plt.pause(0.001)
                                count += 1
                    except Exception as e:
                        print(f"Error in update thread: {e}")
                    
                    # Sleep to avoid consuming too much CPU
                    time.sleep(0.5)
            
            # Start the update thread
            self.update_thread = threading.Thread(target=update_thread)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            print("Simple plot animation started")
            
        except Exception as e:
            print(f"Failed to start plotting: {e}")
            self.plot_active = False
    
    def run(self, enable_plotting=True):
        """Main loop to receive and process data"""
        if not self.serial_conn:
            print("Serial connection not established. Call connect() first.")
            return
        
        print("Starting data collection. Press Ctrl+C to exit.")
        
        # Start plotting in the background if enabled
        if enable_plotting:
            self.start_plotting()
        
        try:
            while True:
                if self.serial_conn.in_waiting > 0:
                    # Read a line from the serial port
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    
                    # Skip non-JSON lines (diagnostic messages, etc.)
                    if line and line[0] == '{' and line[-1] == '}':
                        # Log the raw JSON
                        self.raw_log_file.write(line + '\n')
                        self.raw_log_file.flush()
                        
                        # Process the data
                        processed_data, summary = self.process_data(line)
                        
                        if processed_data and summary:
                            # Log the processed data
                            self.processed_log_file.write(json.dumps(processed_data) + '\n')
                            self.processed_log_file.flush()
                            
                            # Print summary to console
                            print(summary)
                    else:
                        # Print non-JSON lines as debug info
                        print(f"Debug: {line}")
                
                # Small delay to prevent CPU hogging
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\nData collection stopped by user.")
        finally:
            self.close()

def list_available_ports():
    """List all available serial ports with descriptions."""
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("No serial ports found.")
        return None
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
    
    return ports

def auto_detect_arduino():
    """Try to automatically detect an Arduino device."""
    ports = list(serial.tools.list_ports.comports())
    
    # Look for common Arduino identifiers in the descriptions
    arduino_identifiers = ["arduino", "ch340", "ftdi", "silabs", "usb serial"]
    
    for port in ports:
        description = port.description.lower()
        if any(identifier in description for identifier in arduino_identifiers):
            print(f"Arduino detected on {port.device} - {port.description}")
            return port.device
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Process sensor data from Arduino')
    parser.add_argument('--port', help='Serial port (COM port) to connect to')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate (default: 9600)')
    parser.add_argument('--list', action='store_true', help='List available serial ports and exit')
    parser.add_argument('--no-plot', action='store_true', help='Disable live plotting')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_ports()
        return
    
    # If port not specified, try to auto-detect
    port = args.port
    if not port:
        print("No port specified, attempting to auto-detect Arduino...")
        port = auto_detect_arduino()
        
        if not port:
            print("Arduino not auto-detected. Available ports:")
            ports = list_available_ports()
            
            if not ports:
                print("No serial ports found. Please connect an Arduino and try again.")
                return
            
            # Ask user to select a port
            try:
                selection = input("Enter port number to use (or press Enter to quit): ")
                if not selection:
                    return
                
                port_index = int(selection) - 1
                if 0 <= port_index < len(ports):
                    port = ports[port_index].device
                else:
                    print("Invalid selection.")
                    return
            except ValueError:
                print("Invalid input.")
                return
    
    print(f"Using port: {port}")
    processor = SensorDataProcessor(port, args.baud)
    
    # Check if matplotlib is available for plotting
    if args.no_plot:
        print("Live plotting disabled by user.")
    else:
        try:
            import matplotlib
            print("Live plotting of packet loss enabled.")
        except ImportError:
            print("Matplotlib not available. Live plotting disabled.")
            args.no_plot = True
    
    if processor.connect():
        processor.run(enable_plotting=not args.no_plot)

if __name__ == "__main__":
    main()
