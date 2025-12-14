# Flowmeter Configuration for Aister ATLD-DN50-S
FLOW_METER_CONFIG = {
    'port': 'COM4',          # আপনার পোর্ট
    'baudrate': 9600,        # প্রথমে 9600 চেষ্টা করুন
    'bytesize': 8,
    'parity': 'N',
    'stopbits': 1,
    'timeout': 0.5,          # 0.5 সেকেন্ড টাইমআউট
    'device_address': 1,     # ডিফল্ট অ্যাড্রেস
    'retry_attempts': 5,     # ৫ বার রিট্রাই
}

# Aister Flowmeter Register Map (এক্টুয়াল রেজিস্টার)
REGISTER_MAP = {
    # Instantaneous Flow Rate (m³/h) - 4 bytes float
    'instant_flow': {'address': 0x1010, 'format': 'float_inverse', 'unit': 'm³/h', 'decimals': 3},
    
    # Total Flow (m³) - 4 bytes float
    'total_flow': {'address': 0x1012, 'format': 'float_inverse', 'unit': 'm³', 'decimals': 3},
    
    # Flow Velocity (m/s) - 4 bytes float
    'flow_velocity': {'address': 0x1014, 'format': 'float_inverse', 'unit': 'm/s', 'decimals': 3},
    
    # Flow Percentage (%) - 4 bytes float
    'flow_percentage': {'address': 0x1016, 'format': 'float_inverse', 'unit': '%', 'decimals': 1},
    
    # Forward Total Flow (m³) - 4 bytes float
    'forward_total': {'address': 0x1018, 'format': 'float_inverse', 'unit': 'm³', 'decimals': 3},
    
    # Reverse Total Flow (m³) - 4 bytes float
    'reverse_total': {'address': 0x101A, 'format': 'float_inverse', 'unit': 'm³', 'decimals': 3},
    
    # Pipe Diameter (mm) - 4 bytes float
    'pipe_diameter': {'address': 0x1020, 'format': 'float_inverse', 'unit': 'mm', 'decimals': 1},
    
    # Device Status Register - 2 bytes
    'status': {'address': 0x1000, 'format': 'ushort', 'unit': ''},
    
    # Flow Direction (0=Forward, 1=Reverse) - 2 bytes
    'flow_direction': {'address': 0x1001, 'format': 'ushort', 'unit': ''},
    
    # Alarm Status - 2 bytes
    'alarm_status': {'address': 0x1002, 'format': 'ushort', 'unit': ''},
}

# Flow Direction Mapping
FLOW_DIRECTION = {
    0: "Forward ➡️",
    1: "Reverse ⬅️",
    2: "Stopped ⏸️",
}

# Status Bit Definitions
STATUS_BITS = {
    0: "Power On",
    1: "Measuring",
    2: "Empty Pipe",
    3: "Signal Weak",
    4: "Over Range",
    5: "Reverse Flow",
    6: "Calibration",
    7: "System Error",
}