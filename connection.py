import serial
import struct
import time

def test_com4():
    """Direct COM4 connection test for MODBUS device."""
    print("Testing COM4 connection...")
    
    try:
        # Open serial port
        ser = serial.Serial(
            port='COM4',
            baudrate=9600,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=1
        )
        
        print("✅ COM4 opened successfully")
        
        # Try different MODBUS requests
        test_requests = [
            # Read 2 registers from 0x1010 (Instant Flow)
            [0x01, 0x04, 0x10, 0x10, 0x00, 0x02],
            # Read 2 registers from 0x1012 (Total Flow)
            [0x01, 0x04, 0x10, 0x12, 0x00, 0x02],
            # Read 1 register from 0x1001 (Flow Direction)
            [0x01, 0x04, 0x10, 0x01, 0x00, 0x01],
        ]
        
        for req in test_requests:
            # Add CRC
            crc = 0xFFFF
            for byte in req:
                crc ^= byte
                for _ in range(8):
                    if crc & 0x0001:
                        crc = (crc >> 1) ^ 0xA001
                    else:
                        crc = crc >> 1
            
            req.append(crc & 0xFF)
            req.append((crc >> 8) & 0xFF)
            
            # Send request
            ser.reset_input_buffer()
            ser.write(bytes(req))
            
            # Read response
            time.sleep(0.1)
            response = ser.read(100)
            
            if response:
                print(f"\nRequest: {bytes(req[:-2]).hex()}")
                print(f"Response: {response.hex()}")
                
                if len(response) >= 5:
                    # Try to parse as float
                    if len(response) >= 9:  # 4 data bytes
                        data = response[3:7]
                        try:
                            # Try both byte orders
                            # ABCD order
                            val1 = struct.unpack('>f', data)[0]
                            # CDAB order (inverse)
                            val2 = struct.unpack('>f', bytes([data[2], data[3], data[0], data[1]]))[0]
                            print(f"  Float (ABCD): {val1:.3f}")
                            print(f"  Float (CDAB): {val2:.3f}")
                        except:
                            pass
            
            time.sleep(0.5)
        
        ser.close()
        print("\n✅ Test completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_com4()