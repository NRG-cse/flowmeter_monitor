import sys
import time
from connector import ModbusRTUConnector
from display import FlowMeterDisplay

def select_com_port():
    """Let user select COM port"""
    connector = ModbusRTUConnector()
    ports = connector.list_available_ports()
    
    if not ports:
        print("❌ No COM ports detected!")
        print("Please connect your USB-to-RS485 adapter.")
        input("Press Enter after connecting...")
        ports = connector.list_available_ports()
        if not ports:
            print("❌ Still no ports detected. Check connection.")
            return None
    
    print("\nAvailable COM Ports:")
    for i, port in enumerate(ports, 1):
        print(f"{i}. {port['device']} - {port['description']}")
    
    print(f"{len(ports) + 1}. Auto-detect")
    print(f"{len(ports) + 2}. Manual input")
    
    try:
        choice = input(f"\nSelect port (1-{len(ports) + 2}): ").strip()
        
        if choice == str(len(ports) + 1):
            return None  # Auto-detect
        elif choice == str(len(ports) + 2):
            manual_port = input("Enter COM port (e.g., COM3): ").strip()
            return manual_port if manual_port else None
        else:
            index = int(choice) - 1
            if 0 <= index < len(ports):
                return ports[index]['device']
    except:
        pass
    
    return None

def test_communication(connector):
    """Test communication with device"""
    print("\n🔍 Testing communication...")
    
    # Try different baud rates
    baud_rates = [9600, 19200, 4800, 38400]
    
    for baud in baud_rates:
        print(f"  Trying {baud} baud...")
        connector.config['baudrate'] = baud
        
        if connector.connect():
            # Try to read device info
            model = connector.read_parameter('model_code')
            if model is not None:
                print(f"✅ Connected at {baud} baud")
                print(f"📟 Device Model Code: {model}")
                return True
            connector.disconnect()
    
    return False

def main():
    print("=" * 60)
    print("Aister ATLD-DN50-S Flowmeter Data Display")
    print("=" * 60)
    
    # Select COM port
    selected_port = select_com_port()
    
    # Create connector
    connector = ModbusRTUConnector()
    if selected_port:
        connector.config['port'] = selected_port
    
    # Try to connect
    if not connector.connect():
        print("\n⚠️ Could not auto-connect. Trying manual test...")
        if not test_communication(connector):
            print("\n❌ Failed to establish communication.")
            print("\nPossible issues:")
            print("1. USB-to-RS485 adapter not connected")
            print("2. Wrong COM port selected")
            print("3. Wrong baud rate (try 9600, 19200)")
            print("4. Device address incorrect (default is 1)")
            print("5. Wiring issue (A+, B- swapped)")
            
            response = input("\nDo you want to try scanning registers? (y/n): ")
            if response.lower() == 'y':
                from scanner import scan_registers
                scan_registers()
            
            input("\nPress Enter to exit...")
            return
    
    # Create and run display
    display = FlowMeterDisplay(connector)
    
    # Set update rate
    try:
        rate = float(input("\nEnter update rate in seconds (default 1.0): ") or "1.0")
        if 0.1 <= rate <= 10:
            display.update_interval = rate
    except:
        pass
    
    print("\nStarting real-time display...")
    print("The screen will update like your flowmeter's display.")
    print("Press Ctrl+C to exit at any time.")
    
    time.sleep(2)
    
    # Run the display
    display.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")