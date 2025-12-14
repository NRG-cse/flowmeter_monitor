# real_time_display.py
import os
import time
import struct
import serial
from datetime import datetime

class FlowMeterDisplay:
    def __init__(self):
        self.port = 'COM4'
        self.address = 1
        self.baudrate = 9600
        self.serial = None
        self.connected = False
        
        # Flow direction symbols
        self.direction_symbols = {
            'forward': '→',
            'reverse': '←',
            'stopped': '●'
        }
        
    def connect(self):
        """Connect to flowmeter"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.5
            )
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection error: {e}")
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
    
    def read_float_register(self, register):
        """Read a float value from register"""
        try:
            # MODBUS request
            request = bytearray([
                self.address, 0x04,
                (register >> 8) & 0xFF,
                register & 0xFF,
                0x00, 0x02  # Read 2 registers (4 bytes)
            ])
            
            crc = self.calculate_crc(request)
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            self.serial.reset_input_buffer()
            self.serial.write(request)
            
            # Read response
            response = self.serial.read(9)  # 9 bytes expected
            
            if len(response) == 9:
                # Verify CRC
                crc_received = response[-2] | (response[-1] << 8)
                crc_calculated = self.calculate_crc(response[:-2])
                
                if crc_received == crc_calculated:
                    # Parse float (CDAB byte order)
                    data = response[3:7]
                    value = struct.unpack('>f', bytes([
                        data[2], data[3],
                        data[0], data[1]
                    ]))[0]
                    return value
                    
        except Exception as e:
            pass
            
        return None
    
    def read_ushort_register(self, register):
        """Read a 16-bit unsigned integer"""
        try:
            request = bytearray([
                self.address, 0x04,
                (register >> 8) & 0xFF,
                register & 0xFF,
                0x00, 0x01  # Read 1 register
            ])
            
            crc = self.calculate_crc(request)
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            self.serial.reset_input_buffer()
            self.serial.write(request)
            
            response = self.serial.read(7)
            
            if len(response) == 7:
                data = response[3:5]
                return (data[0] << 8) | data[1]
                
        except:
            pass
            
        return None
    
    def get_flow_data(self):
        """Get all flow data"""
        data = {}
        
        # Read instant flow (0x1010)
        flow = self.read_float_register(0x1010)
        if flow is not None:
            data['flow'] = flow
        else:
            data['flow'] = 0.0
        
        # Read total flow (0x1012)
        total = self.read_float_register(0x1012)
        if total is not None:
            data['total'] = total
        else:
            data['total'] = 0.0
        
        # Read flow velocity (0x1014)
        velocity = self.read_float_register(0x1014)
        if velocity is not None:
            data['velocity'] = velocity
        else:
            data['velocity'] = 0.0
        
        # Read flow direction (0x1016)
        direction = self.read_ushort_register(0x1016)
        if direction is not None:
            if direction == 0:
                data['direction'] = 'forward'
                data['direction_symbol'] = '→'
            elif direction == 1:
                data['direction'] = 'reverse'
                data['direction_symbol'] = '←'
            else:
                data['direction'] = 'stopped'
                data['direction_symbol'] = '●'
        else:
            data['direction'] = 'unknown'
            data['direction_symbol'] = '?'
        
        # Read flow percentage (0x1018)
        percentage = self.read_float_register(0x1018)
        if percentage is not None:
            data['percentage'] = percentage
        else:
            data['percentage'] = 0.0
        
        # Read alarm status (0x1020)
        alarm = self.read_ushort_register(0x1020)
        if alarm is not None:
            data['alarm'] = alarm
            data['has_alarm'] = alarm > 0
        else:
            data['alarm'] = 0
            data['has_alarm'] = False
        
        return data
    
    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_flowmeter_screen(self, data):
        """Display like actual flowmeter screen"""
        self.clear_screen()
        
        print("╔══════════════════════════════════════════════════════════╗")
        
        # Title
        title = "AISTER ATLD-DN50-S"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"║ {title:^40} {timestamp:^18} ║")
        
        print("╠══════════════════════════════════════════════════════════╣")
        
        # Main flow display
        flow_value = data.get('flow', 0.0)
        direction_symbol = data.get('direction_symbol', '→')
        
        if flow_value >= 0:
            flow_display = f"{flow_value:9.3f}"
        else:
            flow_display = f"{flow_value:9.3f}"
        
        print(f"║                                                          ║")
        print(f"║         INSTANT FLOW:  {direction_symbol} {flow_display} m³/h      ║")
        print(f"║                                                          ║")
        
        print("╠══════════════════════════════════════════════════════════╣")
        
        # Secondary parameters
        velocity = data.get('velocity', 0.0)
        percentage = data.get('percentage', 0.0)
        total = data.get('total', 0.0)
        
        print(f"║ Velocity: {velocity:7.3f} m/s   Flow %: {percentage:6.1f} %      ║")
        print(f"║ Total Flow: {total:10.3f} m³                           ║")
        
        # Flow direction
        direction = data.get('direction', 'unknown').upper()
        print(f"║ Direction: {direction:^10}                             ║")
        
        # Alarm status
        if data.get('has_alarm', False):
            print(f"║ ⚠️  ALARM ACTIVE! (Code: {data.get('alarm', 0)})                 ║")
        else:
            print(f"║ ✅ STATUS: NORMAL                                ║")
        
        print("╠══════════════════════════════════════════════════════════╣")
        
        # Connection info
        print(f"║ COM4 | Address: {self.address:03d} | DN50 | {datetime.now().strftime('%H:%M:%S')} ║")
        
        print("╚══════════════════════════════════════════════════════════╝")
        
        # Instructions
        print("\n  [Flow Display]")
        print("  → = Forward flow")
        print("  ← = Reverse flow")
        print("  Press Ctrl+C to exit")
    
    def run(self):
        """Main display loop"""
        print("Connecting to flowmeter...")
        
        if not self.connect():
            print("Failed to connect!")
            return
        
        print("Connected! Starting real-time display...")
        time.sleep(1)
        
        try:
            while True:
                data = self.get_flow_data()
                self.display_flowmeter_screen(data)
                time.sleep(1)  # Update every second
                
        except KeyboardInterrupt:
            print("\n\nStopping display...")
        finally:
            if self.serial and self.serial.is_open:
                self.serial.close()
            print("Disconnected")

def main():
    display = FlowMeterDisplay()
    display.run()

if __name__ == "__main__":
    main()