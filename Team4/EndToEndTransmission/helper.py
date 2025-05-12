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
import numpy as np

class SensorDataProcessor:
    def __init__(self, com_port, baud_rate=9600, rolling_window=40):
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.raw_log_file = None
        self.processed_log_file = None
        self.rolling_window = rolling_window  # Size of the rolling window for averaging
        
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
        self.rolling_loss_percentage = deque(maxlen=100)  # New for rolling average
        self.rssi_values = deque(maxlen=100)
        
        # Window for calculating true rolling packet loss
        # This will track actual packet reception success/failure in the window
        self.packet_window = deque(maxlen=rolling_window)  # 1 for received, 0 for lost
        
        # Cumulative counters (for overall statistics)
        self.total_packets_received = 0
        self.total_packets_lost = 0
        self.prev_sequence = None  # Track previous sequence number to detect losses
        self.plot_active = False
        
        # Add packet rate tracking
        self.packet_rates = deque(maxlen=100)
    
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
    
    def calculate_rolling_loss_percentage(self):
        """Calculate actual rolling packet loss percentage based on recent packet history"""
        if not self.packet_window:
            return 0.0
            
        # Count number of lost packets (0s) in the window
        lost_packets = self.packet_window.count(0)
        total_packets = len(self.packet_window)
        
        # Calculate percentage
        if total_packets > 0:
            return (lost_packets / total_packets) * 100
        return 0.0
    
    def process_data(self, json_data):
        """Process the sensor data and extract useful information"""
        try:
            # Parse the JSON data
            data = json.loads(json_data)
            
            # Get current time for the log
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            timestamp = datetime.datetime.now()
            
            rssi = data.get('rssi', 0)
            self.rssi_values.append(rssi)

            # Calculate cardinal direction from yaw
            cardinal_direction = self._get_cardinal_direction(data.get('yaw', 0))
            
            # Get packet sequence and analyze packet loss
            current_sequence = data.get('sequence', 0)
            
            with self.plot_lock:
                # Increment total received counter
                self.total_packets_received += 1
                
                # Check for packet loss by analyzing sequence numbers
                packets_lost_now = 0
                if self.prev_sequence is not None:
                    # Calculate how many packets we expected vs. received
                    expected_sequence = (self.prev_sequence + 1) % 65536  # Assuming 16-bit sequence counter
                    if current_sequence != expected_sequence:
                        # Calculate how many packets were lost (handle wraparound)
                        if current_sequence > expected_sequence:
                            packets_lost_now = current_sequence - expected_sequence
                        else:
                            packets_lost_now = (65536 - expected_sequence) + current_sequence
                        
                        # Update total packets lost
                        self.total_packets_lost += packets_lost_now
                        
                        # Add lost packet markers to the window (0 = lost packet)
                        for _ in range(packets_lost_now):
                            self.packet_window.append(0)
                
                # Store this sequence for next comparison
                self.prev_sequence = current_sequence
                
                # Add received packet marker to window (1 = received packet)
                self.packet_window.append(1)
                
                # Calculate instantaneous loss percentage (overall since start)
                if self.total_packets_received + self.total_packets_lost > 0:
                    loss_percent = (self.total_packets_lost / (self.total_packets_received + self.total_packets_lost)) * 100
                else:
                    loss_percent = 0
                
                # Calculate actual rolling percentage based on window
                rolling_loss = self.calculate_rolling_loss_percentage()
                
                # Update plot data collections
                self.time_data.append(timestamp)
                self.packets_received.append(self.total_packets_received)
                self.packets_lost.append(self.total_packets_lost)
                self.loss_percentage.append(loss_percent)
                self.rolling_loss_percentage.append(rolling_loss)
            
            # Create a processed data record
            processed_data = {
                "time": current_time,
                "arduino_time_ms": data.get('timestamp', 0),
                "packet": {
                    "sequence": current_sequence,
                    "packets_lost_now": packets_lost_now,
                    "total_packets_lost": self.total_packets_lost,
                    "total_packets_received": self.total_packets_received,
                    "overall_loss_percentage": loss_percent,
                    "rolling_loss_percentage": rolling_loss,
                    "window_size": self.rolling_window,
                    "packet_rate": data.get('packet_rate', 0.0)  # Add packet rate
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
                },
                "rssi": rssi
            }
            
            # Update packet rate for plotting
            self.packet_rates.append(data.get('packet_rate', 0.0))
            
            # Create a human-readable summary
            window_info = f"last {len(self.packet_window)}/{self.rolling_window} packets"
            summary = (
                f"Time: {current_time}\n"
                f"Packet: Seq={current_sequence} "
                f"(Lost now: {packets_lost_now}, Total lost: {self.total_packets_lost})\n"
                f"Rate: {data.get('packet_rate', 0.0):.2f} packets/sec\n"
                f"Loss Rate: {loss_percent:.2f}% (Overall), {rolling_loss:.2f}% ({window_info})\n"
                f"Orientation: Pitch={data.get('pitch', 0):.2f}°, "
                f"Roll={data.get('roll', 0):.2f}°, "
                f"Yaw={data.get('yaw', 0):.2f}° ({cardinal_direction})\n"
                f"Acceleration: X={data.get('accel_x', 0):.2f}, "
                f"Y={data.get('accel_y', 0):.2f}, "
                f"Z={data.get('accel_z', 0):.2f} m/s²\n"
                f"Radar: {data.get('distance', 0):.2f} cm @ {cardinal_direction}\n"
                f"RSSI: {rssi} dBm\n"
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
    
    def start_plotting(self):
        """Start the plotting in the main thread using a non-blocking approach"""
        try:
            self.plot_active = True
            
            # Initialize the plot in the main thread
            plt.ion()  # Turn on interactive mode
            self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(2, 1, figsize=(10, 12))
            
            # Setup loss percentage plot
            self.ax1.set_title('Packet Loss Percentage')
            self.ax1.set_xlabel('Sample Number')
            self.ax1.set_ylabel('Loss Percentage (%)')
            self.ax1.set_ylim(0, 10)
            self.ax1.grid(True)
            
            # Setup packet rate plot
            self.ax2.set_title('Packet Rate')
            self.ax2.set_xlabel('Sample Number')
            self.ax2.set_ylabel('Packets/Second')
            self.ax2.set_ylim(0, 12)  # Adjust based on expected rates
            self.ax2.grid(True)
            
            # Setup RSSI plot
            self.ax3.set_title('Signal Strength (RSSI)')
            self.ax3.set_xlabel('Sample Number')
            self.ax3.set_ylabel('RSSI (dBm)')
            self.ax3.set_ylim(-130, -40)  # Typical LoRa RSSI range
            self.ax3.grid(True)

            # Create lines for both plots
            self.instant_line, = self.ax1.plot([], [], 'r-', alpha=0.5, label='Overall Loss %')
            self.rolling_line, = self.ax1.plot([], [], 'b-', linewidth=2, label='Rolling Loss %')
            self.rate_line, = self.ax2.plot([], [], 'g-', linewidth=2, label='Packet Rate')
            self.rssi_line, = self.ax3.plot([], [], 'm-', linewidth=2, label='RSSI')
            
            self.ax1.legend()
            self.ax2.legend()
            self.ax3.legend()
            
            plt.tight_layout()
            
            # Add initial text annotation
            self.info_text = self.ax1.text(0.02, 0.95, 
                                         f'Overall Loss: 0.00%\n'
                                         f'Rolling Loss: 0.00% (window={self.rolling_window})\n'
                                         f'Total Packets: 0\n'
                                         f'Lost Packets: 0',
                                         transform=self.ax1.transAxes,
                                         fontsize=10, verticalalignment='top',
                                         bbox=dict(facecolor='white', alpha=0.5))
            
            # Show the plot window
            self.fig.canvas.draw()
            plt.show(block=False)
            
            print(f"Plot initialized in main thread (rolling window: {self.rolling_window} samples)")
            
        except Exception as e:
            print(f"Failed to start plotting: {e}")
            self.plot_active = False
    
    def update_plot(self):
        """Update the plot with current data"""
        if not self.plot_active:
            return
            
        try:
            with self.plot_lock:
                loss_pcts = list(self.loss_percentage)
                rolling_loss_pcts = list(self.rolling_loss_percentage)
                
                if loss_pcts:
                    # Use sample numbers for x-axis
                    sample_nums = list(range(len(loss_pcts)))
                    
                    # Update the line data
                    self.instant_line.set_data(sample_nums, loss_pcts)
                    self.rolling_line.set_data(sample_nums, rolling_loss_pcts)
                    
                    # Update axis limits
                    self.ax1.set_xlim(0, max(10, len(sample_nums)))
                    
                    # Update y-axis if needed - use the max of both datasets
                    max_value = max(max(loss_pcts) if loss_pcts else 0, 
                                    max(rolling_loss_pcts) if rolling_loss_pcts else 0)
                    if max_value > 0:
                        y_max = min(100, max(10, max_value * 1.2))
                        self.ax1.set_ylim(0, y_max)
                    
                    # Update info text
                    latest_loss = loss_pcts[-1] if loss_pcts else 0
                    latest_rolling = rolling_loss_pcts[-1] if rolling_loss_pcts else 0
                    
                    if hasattr(self, 'info_text') and self.info_text:
                        self.info_text.remove()
                    
                    window_info = f"last {len(self.packet_window)}/{self.rolling_window} packets"
                    self.info_text = self.ax1.text(0.02, 0.95, 
                                                 f'Overall Loss: {latest_loss:.2f}%\n'
                                                 f'Rolling Loss: {latest_rolling:.2f}% ({window_info})\n'
                                                 f'Total Packets: {self.total_packets_received}\n'
                                                 f'Lost Packets: {self.total_packets_lost}',
                                                 transform=self.ax1.transAxes,
                                                 fontsize=10, verticalalignment='top',
                                                 bbox=dict(facecolor='white', alpha=0.5))
                    
                    # Redraw the plot
                    self.fig.canvas.draw_idle()
                    self.fig.canvas.flush_events()
                
                # Update packet rate plot
                rate_data = list(self.packet_rates)
                if rate_data:
                    sample_nums = list(range(len(rate_data)))
                    self.rate_line.set_data(sample_nums, rate_data)
                    self.ax2.set_xlim(0, max(10, len(sample_nums)))
                    max_rate = max(rate_data)
                    if max_rate > 0:
                        self.ax2.set_ylim(0, max(12, max_rate * 1.2))
                
                # Update RSSI plot
                rssi_data = list(self.rssi_values)
                if rssi_data:
                    sample_nums = list(range(len(rssi_data)))
                    self.rssi_line.set_data(sample_nums, rssi_data)
                    self.ax3.set_xlim(0, max(10, len(sample_nums)))
                    
                    # RSSI values are typically negative, so find min/max appropriately
                    min_rssi = min(rssi_data)
                    max_rssi = max(rssi_data)
                    
                    # Set y-axis limits with some padding
                    self.ax3.set_ylim(min(min_rssi - 5, -120), max(max_rssi + 5, -40))
                


        except Exception as e:
            print(f"Error updating plot: {e}")
            self.plot_active = False
    
    def run(self, enable_plotting=True):
        """Main loop to receive and process data"""
        if not self.serial_conn:
            print("Serial connection not established. Call connect() first.")
            return
        
        print("Starting data collection. Press Ctrl+C to exit.")
        
        # Start plotting if enabled
        if enable_plotting:
            self.start_plotting()
        
        try:
            last_plot_update = time.time()
            plot_update_interval = 0.1  # Update plot at 10Hz (every 0.1 seconds)
            
            while True:
                # Process any incoming data
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
                
                # Update the plot periodically from the main thread
                current_time = time.time()
                if enable_plotting and self.plot_active and (current_time - last_plot_update >= plot_update_interval):
                    self.update_plot()
                    last_plot_update = current_time
                
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
    parser.add_argument('--window', type=int, default=40, 
                       help='Size of the rolling window for averaging packet loss (default: 20)')
    
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
    processor = SensorDataProcessor(port, args.baud, rolling_window=args.window)
    
    # Check if matplotlib is available for plotting
    if args.no_plot:
        print("Live plotting disabled by user.")
    else:
        try:
            import matplotlib
            print(f"Live plotting of packet loss enabled with rolling window of {args.window} samples.")
        except ImportError:
            print("Matplotlib not available. Live plotting disabled.")
            args.no_plot = True
    
    if processor.connect():
        processor.run(enable_plotting=not args.no_plot)

if __name__ == "__main__":
    main()
