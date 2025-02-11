import time


import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
print(ports)

ser = serial.Serial("COM8", 9600)  # Change to the correct port
ser.write(b"Fake Sensor Data is it fake\n")
ser.close()
