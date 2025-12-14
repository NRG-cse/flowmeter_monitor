# simple_reader.py
import serial
import struct
import time
from datetime import datetime

class SimpleFlowReader:
    def __init__(self, port='COM4', baudrate=9600, address=1):
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.serial = None
        
    def connect(self):
        """Connect to the flowmeter"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1.0,
                write_timeout=1.0
            )
            print(f"✅ Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def calculate_crc(self, data):
        """Calculate MODBUS CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc
    
    def read_register(self, register, count=2):
        """Read MODBUS register"""
        try:
            # Build MODBUS request (Function Code 04 - Read Input Registers)
            request = bytearray([
                self.address,      # Slave address (001 = 1 in decimal)
                0x04,              # Function code 04
                (register >> 8) & 0xFF,  # High byte
                register & 0xFF,         # Low byte
                (count >> 8) & 0xFF,     # High byte of count
                count & 0xFF             # Low byte of count
            ])
            
            # Add CRC
            crc = self.calculate_crc(request)
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            # Send request
            self.serial.reset_input_buffer()
            self.serial.write(request)
            
            # Wait a bit (MODBUS timing)
            time.sleep(0.05)
            
            # Read response
            response = self.serial.read(5 + 2 * count + 2)
            
            if len(response) < 5:
                return None
            
            # Verify CRC
            received_crc = response[-2] | (response[-1] << 8)
            calculated_crc = self.calculate_crc(response[:-2])
            
            if received_crc != calculated_crc:
                return None
            
            # Extract data bytes
            data_bytes = response[3:-2]
            
            if count == 2 and len(data_bytes) == 4:
                # Parse as float (CDAB byte order)
                return struct.unpack('>f', bytes([
                    data_bytes[2], data_bytes[3],
                    data_bytes[0], data_bytes[1]
                ]))[0]
            
            return data_bytes
            
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def read_all_parameters(self):
        """Read all flowmeter parameters"""
        results = {}
        
        # Try common register addresses for Aister flowmeter
        registers = {
            'instant_flow': 0x1010,      # Instantaneous flow rate
            'total_flow': 0x1012,        # Total flow
            'flow_velocity': 0x1014,     # Flow velocity
            'flow_direction': 0x1016,    # Flow direction (0=forward, 1=reverse)
            'flow_percentage': 0x1018,   # Flow percentage
            'alarm_status': 0x1020,      # Alarm status
            'pipe_diameter': 0x1030,     # Pipe diameter
        }
        
        for name, addr in registers.items():
            value = self.read_register(addr, 2)
            if value is not None:
                results[name] = value
                print(f"{name}: {value}")
            time.sleep(0.1)
        
        return results
    
    def continuous_read(self, register=0x1010):
        """Continuously read and display a specific register"""
        print(f"\n📊 Continuous reading from register {hex(register)}")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                value = self.read_register(register, 2)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if value is not None:
                    if register == 0x1010:  # Flow rate
                        print(f"[{timestamp}] Instant Flow: {value:8.3f} m³/h")
                    elif register == 0x1014:  # Velocity
                        print(f"[{timestamp}] Velocity: {value:8.3f} m/s")
                    else:
                        print(f"[{timestamp}] Value: {value}")
                else:
                    print(f"[{timestamp}] ❌ No response")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
    
    def test_all_registers(self):
        """Test reading from various registers"""
        print("\n🔍 Testing register reading...")
        
        test_registers = [
            (0x1000, "Model Code"),
            (0x1002, "Serial Number"),
            (0x1010, "Instant Flow"),
            (0x1012, "Total Flow"),
            (0x1014, "Flow Velocity"),
            (0x1016, "Flow Direction"),
            (0x1018, "Flow Percentage"),
            (0x1020, "Alarm Status"),
            (0x1021, "Device Status"),
        ]
        
        for addr, name in test_registers:
            value = self.read_register(addr, 2)
            if value is not None:
                print(f"{name} ({hex(addr)}): {value}")
            else:
                print(f"{name} ({hex(addr)}): ❌ No response")
            time.sleep(0.1)
    
    def disconnect(self):
        """Disconnect from device"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("🔌 Disconnected")

def main():
    print("=" * 60)
    print("Aister ATLD-DN50-S Simple Reader")
    print("=" * 60)
    
    # Create reader with your settings
    reader = SimpleFlowReader(
        port='COM4',
        baudrate=9600,
        address=1  # MODBUS address 001
    )
    
    # Connect
    if not reader.connect():
        print("Failed to connect. Exiting...")
        return
    
    # Test communication
    print("\nTesting communication...")
    reader.test_all_registers()
    
    # Menu
    while True:
        print("\n" + "=" * 40)
        print("MENU:")
        print("1. Continuous flow rate display")
        print("2. Test all registers")
        print("3. Read all parameters once")
        print("4. Change register address")
        print("5. Exit")
        print("=" * 40)
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == '1':
            reader.continuous_read(0x1010)  # Read instant flow
            
        elif choice == '2':
            reader.test_all_registers()
            
        elif choice == '3':
            data = reader.read_all_parameters()
            if data:
                print("\n📋 Current Parameters:")
                for key, value in data.items():
                    print(f"{key:20}: {value}")
                    
        elif choice == '4':
            try:
                reg = input("Enter register address in hex (e.g., 1010): ").strip()
                if reg.startswith('0x'):
                    reg = int(reg, 16)
                else:
                    reg = int(reg, 16)
                reader.continuous_read(reg)
            except:
                print("Invalid address!")
                
        elif choice == '5':
            break
    
    reader.disconnect()

if __name__ == "__main__":
    main()