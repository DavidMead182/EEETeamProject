import serial

# Open the serial port (COM5) with the same settings as your MCU (115200 baud, 8 data bits, 1 stop bit, no parity)
ser = serial.Serial('COM5', baudrate=9600, timeout=1)  # Set timeout to 1 second

# Read data from the serial port
while True:
    if ser.in_waiting > 0:  # Check if there's data available to read
        data = ser.readline()  # Read a line of data
        print("Received:", data.decode('utf-8').strip())  # Decode byte data to string and remove extra whitespace
