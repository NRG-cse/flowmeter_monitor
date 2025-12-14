# check_ports.py ফাইল তৈরি করুন
import serial.tools.list_ports

def list_com_ports():
    ports = serial.tools.list_ports.comports()
    print("Available COM Ports:")
    for port in ports:
        print(f"Port: {port.device}")
        print(f"  Name: {port.name}")
        print(f"  Description: {port.description}")
        print(f"  HWID: {port.hwid}")
        print(f"  VID:PID: {port.vid}:{port.pid}")
        print("-" * 40)

if __name__ == "__main__":
    list_com_ports()