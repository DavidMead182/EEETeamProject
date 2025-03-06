import serial
import serial.tools.list_ports
import json
import time
import datetime
import math
import argparse
import os

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
    
    def process_data(self, json_data):
        """Process the sensor data and extract useful information"""
        try:
            # Parse the JSON data
            data = json.loads(json_data)
            
            # Get current time for the log
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            # Calculate cardinal direction from yaw
            cardinal_direction = self._get_cardinal_direction(data.get('yaw', 0))
            
            # Create a processed data record
            processed_data = {
                "time": current_time,
                "arduino_time_ms": data.get('timestamp', 0),
                "orientation": {
                    "pitch": data.get('pitch', 0),
                    "roll": data.get('roll', 0),
                    "yaw": data.get('yaw', 0),
                    "cardinal_direction": cardinal_direction
                },
                "radar": {
                    "distance_cm": data.get('distance', 0),
                    "direction": cardinal_direction
                }
            }
            
            # Create a human-readable summary
            summary = (
                f"Time: {current_time}\n"
                f"Orientation: Pitch={data.get('pitch', 0):.2f}°, "
                f"Roll={data.get('roll', 0):.2f}°, "
                f"Yaw={data.get('yaw', 0):.2f}° ({cardinal_direction})\n"
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
    
    def run(self):
        """Main loop to receive and process data"""
        if not self.serial_conn:
            print("Serial connection not established. Call connect() first.")
            return
        
        print("Starting data collection. Press Ctrl+C to exit.")
        
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
    if processor.connect():
        processor.run()

if __name__ == "__main__":
    main()
