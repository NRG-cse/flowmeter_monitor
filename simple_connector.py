import serial
import struct
import time

class SimpleFlowMeterReader:
    def __init__(self, port='COM4', baudrate=9600, address=1):
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.serial = None
        
    def connect(self):
        """সরাসরি কানেক্ট করুন"""
        try:
            print(f"🔌 Connecting to {self.port} at {self.baudrate} baud...")
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.5,
                write_timeout=0.5
            )
            
            # Test connection
            test_data = self.read_register(0x1010, 2)
            if test_data:
                print("✅ Connection successful!")
                return True
            else:
                print("⚠️ Connected but no data")
                return False
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def calculate_crc(self, data):
        """CRC16-MODBUS calculation"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc
    
    def read_register(self, address, count=2):
        """রেজিস্টার পড়ুন"""
        try:
            # MODBUS RTU request
            request = bytearray([
                self.address,           # Slave address
                0x04,                   # Function 04 (Read Input Registers)
                (address >> 8) & 0xFF,  # Address high byte
                address & 0xFF,         # Address low byte
                0x00,                   # Quantity high byte
                count                   # Quantity low byte
            ])
            
            # Calculate CRC
            crc = self.calculate_crc(request)
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            # Send request
            self.serial.reset_input_buffer()
            self.serial.write(request)
            
            # Read response
            response = self.serial.read(5 + 2 * count + 2)
            
            if len(response) < 7:
                return None
            
            # Verify response
            if response[0] != self.address:
                return None
            
            # Check CRC
            crc_received = response[-2] | (response[-1] << 8)
            crc_calculated = self.calculate_crc(response[:-2])
            
            if crc_received != crc_calculated:
                return None
            
            # Return data bytes
            return response[3:-2]
            
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def parse_float_inverse(self, data):
        """Parse 4 bytes as float (CDAB order)"""
        if data and len(data) == 4:
            try:
                # Convert CDAB to ABCD (big-endian)
                return struct.unpack('>f', bytes([data[2], data[3], data[0], data[1]]))[0]
            except:
                return None
        return None
    
    def read_instant_flow(self):
        """ইন্সট্যান্ট ফ্লো রেট পড়ুন"""
        data = self.read_register(0x1010, 2)
        if data:
            flow = self.parse_float_inverse(data)
            return flow if flow is not None else 0.0
        return None
    
    def read_all_data(self):
        """সব ডাটা একসাথে পড়ুন"""
        data = {}
        
        # Instant Flow
        flow_data = self.read_register(0x1010, 2)
        if flow_data:
            data['instant_flow'] = self.parse_float_inverse(flow_data)
        
        # Total Flow
        total_data = self.read_register(0x1012, 2)
        if total_data:
            data['total_flow'] = self.parse_float_inverse(total_data)
        
        # Flow Velocity
        velocity_data = self.read_register(0x1014, 2)
        if velocity_data:
            data['flow_velocity'] = self.parse_float_inverse(velocity_data)
        
        # Flow Percentage
        percent_data = self.read_register(0x1016, 2)
        if percent_data:
            data['flow_percentage'] = self.parse_float_inverse(percent_data)
        
        # Flow Direction
        dir_data = self.read_register(0x1001, 1)
        if dir_data and len(dir_data) >= 2:
            data['flow_direction'] = (dir_data[0] << 8) | dir_data[1]
        
        return data
    
    def disconnect(self):
        """ডিসকানেক্ট করুন"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("🔌 Disconnected")