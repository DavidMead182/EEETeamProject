import json
import serial
import signal
import sys#
import time
from datetime import datetime

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(sig, frame):
    """Handle Ctrl+C interrupt"""
    global shutdown_flag
    print("\nShutting down gracefully...")
    shutdown_flag = True

def print_microcontroller_data(port: str, baudrate: int = 115200):
    """
    Read and print JSON data from a microcontroller using interrupt-driven I/O.
    Press Ctrl+C to stop.
    """
    ser = None
    try:
        # Set up serial connection
        ser = serial.Serial(port, baudrate, timeout=0)  # Non-blocking mode
        print(f"Connected to {port} at {baudrate} baud")
        print("Waiting for data... (Press Ctrl+C to stop)\n")

        buffer = ""
        while not shutdown_flag:
            if ser.in_waiting > 0:
                # Read available bytes and decode
                buffer += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                
                # Process complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            data['received_at'] = datetime.now().isoformat()
                            print("Received:", json.dumps(data, indent=2))
                        except json.JSONDecodeError:
                            print(f"⚠️ Invalid JSON: {line}")
            
            # Small sleep to prevent CPU overload
            time.sleep(0.01)

    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
            print("🔌 Serial connection closed")

if __name__ == "__main__":
    # Register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)

    # Example usage (replace with your port)
    #print_microcontroller_data('/dev/ttyUSB0')  # Linux
    print_microcontroller_data('COM5')        # Windows