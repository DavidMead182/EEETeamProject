import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
identifier = "USB Serial Device"
for port in ports:
    print(f"Port: {port.device} - {port.description}")
 
if identifier in port.description:
    print(port.description)
else:
    print("can't find device")