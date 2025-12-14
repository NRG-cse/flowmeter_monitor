from connector import ModbusRTUConnector
from config import REGISTER_MAP
from datetime import datetime

class FlowMeter:
    def __init__(self, config=None):
        self.connector = ModbusRTUConnector(config)
        self.connected = False
        self.last_read_time = None

    def connect(self):
        self.connected = self.connector.connect()
        if self.connected:
            self.last_read_time = datetime.now()
        return self.connected

    def _get_total_flow(self, int_addr, dec_addr):
        """Calculate total flow (integer + decimal parts)"""
        int_part = self.connector.read_register(int_addr, 'long_inverse', 2)
        dec_part = self.connector.read_register(dec_addr, 'float_inverse', 2)
        
        if int_part is not None and dec_part is not None:
            total = int_part + dec_part
            if total < 0:
                total = 0
            return total
        return None

    def read_all_parameters(self):
        if not self.connected:
            raise ConnectionError("Device not connected")
        
        results = {}
        
        try:
            # Read measurements
            for param, config in REGISTER_MAP.items():
                if param == 'alarms':
                    continue
                if 'total' in param:  # Skip totals (handled separately)
                    continue
                
                count = 2 if config['format'] in ('float_inverse', 'long_inverse') else 1
                value = self.connector.read_register(
                    config['address'],
                    format_type=config['format'],
                    count=count
                )
                
                if value is not None:
                    # Apply formatting/limits if needed
                    if param == 'flow_percentage' and value > 100:
                        value = 100
                    elif param == 'flow_percentage' and value < 0:
                        value = 0
                    
                results[param] = value
            
            # Calculate total flows
            results['positive_total'] = self._get_total_flow(
                REGISTER_MAP['positive_total_int']['address'],
                REGISTER_MAP['positive_total_dec']['address']
            )
            results['negative_total'] = self._get_total_flow(
                REGISTER_MAP['negative_total_int']['address'],
                REGISTER_MAP['negative_total_dec']['address']
            )
            
            # Read alarms
            alarms = {}
            for alarm, addr in REGISTER_MAP['alarms'].items():
                alarm_value = self.connector.read_register(addr, 'ushort', 1)
                alarms[alarm] = bool(alarm_value) if alarm_value is not None else False
            results['alarms'] = alarms
            
            self.last_read_time = datetime.now()
            
        except Exception as e:
            print(f"Error reading parameters: {e}")
            # Return partial data if available
            if not results:
                return None
        
        return results

    def disconnect(self):
        self.connected = False
        self.connector.disconnect()

class DataLogger:
    def __init__(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'flowmeter_data_{timestamp}.csv'
        self.filename = filename
        self._initialize_file()

    def _initialize_file(self):
        import os
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write("timestamp,instant_flow(m3/h),instant_velocity(m/s),flow_percentage(%),conductivity(uS/cm),"
                        "positive_total(m3),negative_total(m3),upper_alarm,lower_alarm,empty_pipe_alarm,system_alarm\n")

    def log_data(self, data):
        try:
            timestamp = datetime.now().isoformat()
            row = [
                timestamp,
                data.get('instant_flow', ''),
                data.get('instant_velocity', ''),
                data.get('flow_percentage', ''),
                data.get('conductivity', ''),
                data.get('positive_total', ''),
                data.get('negative_total', ''),
                int(data.get('alarms', {}).get('upper', False)),
                int(data.get('alarms', {}).get('lower', False)),
                int(data.get('alarms', {}).get('empty_pipe', False)),
                int(data.get('alarms', {}).get('system', False))
            ]
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(','.join(map(str, row)) + '\n')
            return True
        except Exception as e:
            print(f"Logging error: {str(e)}")
            return False