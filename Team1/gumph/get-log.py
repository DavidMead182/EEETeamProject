
import serial
import time

port = '/dev/ttyACM1'
baudrate = 115200
log_filename = 'imu_data_OpenIMU.txt'

def open_serial(port, baudrate):
    return serial.Serial(port, baudrate, timeout=1)

while True:
    try:
        print("Opening serial port...")
        ser = open_serial(port, baudrate)
        time.sleep(2)  # Allow Arduino to reset

        with open(log_filename, 'a') as f:
            print("Logging data. Press Ctrl+C to stop.")
            while True:
                try:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8', errors='ignore').strip()
                        f.write(line + '\n')
                        print(line)
                except serial.SerialException as e:
                    print("Serial error:", e)
                    break  # Exit inner loop to reconnect
    except KeyboardInterrupt:
        print("User interrupted. Exiting.")
        break
    except Exception as e:
        print("Unexpected error:", e)
        time.sleep(5)  # Wait before retrying

