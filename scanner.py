import time
from connector import ModbusRTUConnector

def scan_registers(start=0x1000, end=0x1040):
    """Scan registers to find active data"""
    connector = ModbusRTUConnector()
    
    print("\n" + "="*60)
    print("Register Scanner")
    print("="*60)
    
    if not connector.connect():
        print("❌ Could not connect to device")
        return
    
    print(f"\nScanning registers {hex(start)} to {hex(end)}...\n")
    
    found_registers = []
    
    for addr in range(start, end + 1, 2):
        try:
            # Try as 2 registers (4 bytes - float/long)
            data = connector.read_holding_register(addr, 2)
            if data and len(data) == 4:
                # Try to parse as float
                float_val = connector.parse_float_inverse(data)
                if float_val is not None and float_val != 0:
                    found_registers.append({
                        'address': hex(addr),
                        'type': 'float_inverse',
                        'value': float_val,
                        'raw': data.hex()
                    })
                    print(f"[{hex(addr)}] float_inverse = {float_val:.4f}")
            
            # Also try as single register
            time.sleep(0.05)
            single_val = connector.read_holding_register(addr, 1)
            if single_val is not None and single_val != 0:
                found_registers.append({
                    'address': hex(addr),
                    'type': 'ushort',
                    'value': single_val,
                    'raw': hex(single_val)
                })
                print(f"[{hex(addr)}] ushort = {single_val}")
                
        except Exception as e:
            continue
    
    connector.disconnect()
    
    print("\n" + "="*60)
    print(f"Scan complete. Found {len(found_registers)} active registers.")
    
    if found_registers:
        print("\nSuggested register map additions:")
        for reg in found_registers[:10]:  # Show first 10
            print(f"    '{hex(reg['address'])}': {{'address': {reg['address']}, 'format': '{reg['type']}'}},")
    
    return found_registers

if __name__ == "__main__":
    scan_registers()