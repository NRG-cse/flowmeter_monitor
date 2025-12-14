# troubleshooter.py
import serial
import time

def test_modbus_communication():
    """Test basic MODBUS communication"""
    
    print("=" * 60)
    print("Flowmeter Communication Troubleshooter")
    print("=" * 60)
    
    # Try different configurations
    configs = [
        {'port': 'COM4', 'baudrate': 9600, 'address': 1},
        {'port': 'COM4', 'baudrate': 19200, 'address': 1},
        {'port': 'COM4', 'baudrate': 4800, 'address': 1},
        {'port': 'COM4', 'baudrate': 9600, 'address': 2},
    ]
    
    for config in configs:
        print(f"\nTrying: Port={config['port']}, Baud={config['baudrate']}, Address={config['address']}")
        
        try:
            ser = serial.Serial(
                port=config['port'],
                baudrate=config['baudrate'],
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            
            # Test with Function 04 (Read Input Registers)
            test_register = 0x1010  # Common flow register
            
            request = bytearray([
                config['address'], 0x04,
                (test_register >> 8) & 0xFF,
                test_register & 0xFF,
                0x00, 0x02  # Read 2 registers
            ])
            
            # Calculate CRC
            crc = 0xFFFF
            for byte in request:
                crc ^= byte
                for _ in range(8):
                    if crc & 0x0001:
                        crc >>= 1
                        crc ^= 0xA001
                    else:
                        crc >>= 1
            
            request.append(crc & 0xFF)
            request.append((crc >> 8) & 0xFF)
            
            ser.write(request)
            time.sleep(0.1)
            
            response = ser.read(100)
            
            if len(response) > 0:
                print(f"✅ Response received: {len(response)} bytes")
                print(f"   Raw response: {response.hex()}")
                
                if len(response) >= 9:
                    print("   ✓ Valid MODBUS frame")
                    
                    # Check address
                    if response[0] == config['address']:
                        print(f"   ✓ Correct address: {response[0]}")
                    else:
                        print(f"   ✗ Wrong address. Got: {response[0]}, Expected: {config['address']}")
            else:
                print("❌ No response")
            
            ser.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Troubleshooting Tips:")
    print("1. Check RS485 wiring (A+, B-)")
    print("2. Try swapping A+ and B- wires")
    print("3. Check power supply to flowmeter (DC24V)")
    print("4. Ensure proper grounding")
    print("5. Try different baud rates")
    print("=" * 60)

if __name__ == "__main__":
    test_modbus_communication()