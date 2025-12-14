import serial
import time
import struct
import threading
from serial.tools.list_ports import comports
from config import FLOW_METER_CONFIG, REGISTER_MAP

class ModbusRTUConnector:
    def __init__(self, config=None):
        self.config = config or FLOW_METER_CONFIG.copy()
        self.serial = None
        self.lock = threading.Lock()
        self.last_request = 0
        self.connected = False
        
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
    
    def list_available_ports(self):
        """List all available COM ports"""
        ports = []
        for port in comports():
            ports.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports
    
    def connect(self, port=None):
        """Connect to flowmeter"""
        with self.lock:
            if port:
                self.config['port'] = port
            
            if not self.config['port']:
                # Auto-detect
                ports = self.list_available_ports()
                if not ports:
                    print("❌ No COM ports found!")
                    return False
                
                # Try common RS485 adapters
                for p in ports:
                    if any(keyword in p['description'].upper() for keyword in 
                           ['USB', 'RS485', 'SERIAL', 'CH340', 'FTDI', 'CP210']):
                        self.config['port'] = p['device']
                        print(f"🔍 Auto-detected: {p['device']} - {p['description']}")
                        break
                
                if not self.config['port']:
                    self.config['port'] = ports[0]['device']
                    print(f"📌 Using first available port: {self.config['port']}")
            
            try:
                print(f"🔌 Connecting to {self.config['port']}...")
                self.serial = serial.Serial(
                    port=self.config['port'],
                    baudrate=self.config['baudrate'],
                    bytesize=self.config['bytesize'],
                    parity=self.config['parity'],
                    stopbits=self.config['stopbits'],
                    timeout=self.config['timeout'],
                    write_timeout=1
                )
                
                # Test communication
                if self.test_connection():
                    self.connected = True
                    print(f"✅ Connected successfully to {self.config['port']}")
                    return True
                else:
                    self.serial.close()
                    self.connected = False
                    return False
                    
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                self.connected = False
                return False
    
    def test_connection(self):
        """Test if device responds"""
        try:
            # Try to read device model
            response = self.read_holding_register(0x1000, 1)
            return response is not None
        except:
            return False
    
    def _ensure_delay(self):
        """Maintain minimum delay between MODBUS requests"""
        min_delay = 0.0035  # 3.5ms minimum for 9600 baud
        elapsed = time.time() - self.last_request
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
    
    def read_holding_register(self, address, count=1):
        """Read holding registers (Function 03)"""
        with self.lock:
            self._ensure_delay()
            
            # Build request
            request = bytearray([
                self.config['device_address'],  # Slave address
                0x03,                           # Function 03 (Read Holding Registers)
                (address >> 8) & 0xFF,          # High byte of address
                address & 0xFF,                 # Low byte of address
                (count >> 8) & 0xFF,           # High byte of count
                count & 0xFF                    # Low byte of count
            ])
            
            # Add CRC
            crc = self.calculate_crc(request)
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            try:
                # Send request
                self.serial.reset_input_buffer()
                self.serial.write(request)
                self.last_request = time.time()
                
                # Read response
                response = self.serial.read(5 + 2 * count + 2)
                
                if len(response) < 5:
                    return None
                
                # Verify CRC
                received_crc = response[-2] | (response[-1] << 8)
                calculated_crc = self.calculate_crc(response[:-2])
                
                if received_crc != calculated_crc:
                    print(f"⚠️ CRC error: {hex(received_crc)} != {hex(calculated_crc)}")
                    return None
                
                # Extract data bytes
                data_bytes = response[3:-2]
                
                # Parse based on count
                if count == 1:
                    # Single register (2 bytes)
                    return (data_bytes[0] << 8) | data_bytes[1]
                elif count == 2:
                    # Two registers (4 bytes) - Float or Long
                    return data_bytes
                else:
                    # Multiple registers
                    return data_bytes
                    
            except Exception as e:
                print(f"⚠️ Read error: {e}")
                return None
    
    def read_input_register(self, address, count=1):
        """Read input registers (Function 04)"""
        with self.lock:
            self._ensure_delay()
            
            # Build request
            request = bytearray([
                self.config['device_address'],  # Slave address
                0x04,                           # Function 04 (Read Input Registers)
                (address >> 8) & 0xFF,
                address & 0xFF,
                (count >> 8) & 0xFF,
                count & 0xFF
            ])
            
            # Add CRC
            crc = self.calculate_crc(request)
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            try:
                # Send request
                self.serial.reset_input_buffer()
                self.serial.write(request)
                self.last_request = time.time()
                
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
                return response[3:-2]
                    
            except Exception as e:
                print(f"Read error: {e}")
                return None
    
    def parse_float_inverse(self, data_bytes):
        """Parse 4 bytes as float with inverse byte order (CDAB)"""
        if len(data_bytes) != 4:
            return None
        try:
            # Convert CDAB to ABCD (big-endian)
            return struct.unpack('>f', bytes([data_bytes[2], data_bytes[3], 
                                              data_bytes[0], data_bytes[1]]))[0]
        except:
            return None
    
    def parse_long_inverse(self, data_bytes):
        """Parse 4 bytes as long with inverse byte order"""
        if len(data_bytes) != 4:
            return None
        try:
            return struct.unpack('>l', bytes([data_bytes[2], data_bytes[3], 
                                              data_bytes[0], data_bytes[1]]))[0]
        except:
            return None
    
    def read_parameter(self, param_name):
        """Read a specific parameter from register map"""
        if param_name not in REGISTER_MAP:
            return None
        
        config = REGISTER_MAP[param_name]
        address = config['address']
        format_type = config.get('format', 'ushort')
        
        if format_type == 'float_inverse':
            data = self.read_holding_register(address, 2)
            if data:
                return self.parse_float_inverse(data)
        
        elif format_type == 'ushort':
            return self.read_holding_register(address, 1)
        
        elif format_type == 'string':
            length = config.get('length', 8)
            registers = (length + 1) // 2
            data = self.read_holding_register(address, registers)
            if data:
                return data.decode('ascii', errors='ignore').strip('\x00')
        
        return None
    
    def read_all_parameters(self):
        """Read all configured parameters"""
        results = {}
        
        for param_name, config in REGISTER_MAP.items():
            value = self.read_parameter(param_name)
            if value is not None:
                results[param_name] = value
        
        return results
    
    def disconnect(self):
        """Disconnect from device"""
        with self.lock:
            if self.serial and self.serial.is_open:
                self.serial.close()
                self.connected = False
                print("🔌 Disconnected")