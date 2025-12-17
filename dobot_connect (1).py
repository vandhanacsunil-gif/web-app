from pydobot import Dobot
import serial.tools.list_ports

# Auto-detect Dobot COM Port
ports = list(serial.tools.list_ports.comports())
port = None

for p in ports:
    if "USB" in p.description or "Dobot" in p.description or "CH340" in p.description:
        port = p.device
        break

if port is None:
    print("Dobot not found! Please check USB connection.")
    exit()

print("Connecting to:", port)

# Connect Dobot
device = Dobot(port)

# Read the current pose
pose = device.pose()
print("Current Dobot position:", pose)

# Move the arm (x, y, z, r)
device.move_to(200, 0, 50, 0)
device.move_to(200, 0, 10, 0)
device.move_to(150, 0, 10, 0)
device.move_to(259, 0, -8.6, 0)
device.move_to(259, 0, -131.8, 0)
device.move_to(161.2, 158.4, 2, 0)
device.move_to(161.2, 158.4, -130.7, 0)
device.move_to(161.2, 158.4, -11.9, 0 )
device.move_to(259, 0, -8.6, 0)

print("Movement completed!")

device.close()

