import os
import time
from datetime import datetime
from connector import ModbusRTUConnector
from config import REGISTER_MAP, ALARM_BITS, STATUS_BITS

class FlowMeterDisplay:
    def __init__(self, connector):
        self.connector = connector
        self.screen_width = 80
        self.update_interval = 1.0  # seconds
        
    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def draw_border(self):
        """Draw border around display"""
        print("╔" + "═" * (self.screen_width - 2) + "╗")
    
    def draw_footer(self):
        """Draw footer"""
        print("╚" + "═" * (self.screen_width - 2) + "╝")
    
    def draw_header(self):
        """Draw header with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = "Aister ATLD-DN50-S Electromagnetic Flowmeter"
        header = f"{title} | {timestamp}"
        print("║" + header.center(self.screen_width - 2) + "║")
    
    def draw_separator(self):
        """Draw separator line"""
        print("╟" + "─" * (self.screen_width - 2) + "╢")
    
    def format_value(self, value, config):
        """Format value with proper decimals and unit"""
        if value is None:
            return "---"
        
        unit = config.get('unit', '')
        decimals = config.get('decimals', 2)
        
        if isinstance(value, float):
            return f"{value:.{decimals}f} {unit}"
        elif isinstance(value, int):
            return f"{value} {unit}"
        else:
            return f"{value} {unit}"
    
    def display_main_screen(self, data):
        """Display main screen like flowmeter LCD"""
        self.clear_screen()
        self.draw_border()
        self.draw_header()
        self.draw_separator()
        
        # Instant Flow (Large display)
        flow_value = data.get('instant_flow')
        if flow_value is not None:
            flow_str = f"{flow_value:>8.3f} m³/h"
        else:
            flow_str = "---.--- m³/h"
        
        print("║" + " " * ((self.screen_width - len(flow_str)) // 2 - 1) + 
              f"INSTANT FLOW: {flow_str}" + 
              " " * ((self.screen_width - len(flow_str)) // 2 - 4) + "║")
        
        self.draw_separator()
        
        # Secondary parameters in 2 columns
        params = [
            ('Total Flow', 'total_flow', 'm³'),
            ('Flow Velocity', 'flow_velocity', 'm/s'),
            ('Flow %', 'flow_percentage', '%'),
            ('Pipe Diameter', 'pipe_diameter', 'mm'),
        ]
        
        col_width = (self.screen_width - 4) // 2
        
        for i in range(0, len(params), 2):
            row = ""
            for j in range(2):
                if i + j < len(params):
                    label, key, default_unit = params[i + j]
                    value = data.get(key)
                    config = REGISTER_MAP.get(key, {'unit': default_unit, 'decimals': 3})
                    
                    if value is not None:
                        if isinstance(value, float):
                            display_value = f"{value:.3f}"
                        else:
                            display_value = str(value)
                    else:
                        display_value = "---"
                    
                    unit = config.get('unit', default_unit)
                    cell = f"{label}: {display_value} {unit}"
                    row += cell.ljust(col_width)
                else:
                    row += "".ljust(col_width)
            
            print("║ " + row + " ║")
        
        self.draw_separator()
        
        # Alarm Status
        alarm_value = data.get('alarm_status', 0)
        if alarm_value == 0:
            alarm_status = "🟢 NORMAL"
        else:
            active_alarms = []
            for bit, desc in ALARM_BITS.items():
                if alarm_value & (1 << bit):
                    active_alarms.append(desc)
            alarm_status = "🔴 " + ", ".join(active_alarms[:2])
        
        print("║ ALARM: " + alarm_status.ljust(self.screen_width - 11) + "║")
        
        # Device Status
        status_value = data.get('device_status', 0)
        status_list = []
        for bit, desc in STATUS_BITS.items():
            if status_value & (1 << bit):
                status_list.append(desc)
        
        status_str = " | ".join(status_list) if status_list else "STANDBY"
        print("║ STATUS: " + status_str.ljust(self.screen_width - 11) + "║")
        
        self.draw_footer()
        
        # Footer info
        print(f"  COM Port: {self.connector.config['port']} | Address: {self.connector.config['device_address']}")
        print(f"  Update: {self.update_interval}s | Press Ctrl+C to exit")
    
    def run(self):
        """Main display loop"""
        print("Starting flowmeter display...")
        
        try:
            while True:
                if not self.connector.connected:
                    print("❌ Not connected. Trying to reconnect...")
                    if not self.connector.connect():
                        time.sleep(2)
                        continue
                
                # Read data
                data = self.connector.read_all_parameters()
                
                # Display data
                if data:
                    self.display_main_screen(data)
                else:
                    print("⚠️ No data received from device")
                
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\n\nExiting display...")
        finally:
            self.connector.disconnect()