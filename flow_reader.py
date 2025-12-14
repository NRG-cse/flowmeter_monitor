from modbus_client import get_client
from config import FLOW_REGISTER, SLAVE_ID, FACTOR

client = get_client()

def read_flow():
    result = client.read_holding_registers(FLOW_REGISTER, 1, slave=SLAVE_ID)
    if result.isError():
        return None

    raw = result.registers[0]
    flow_m3_h = (raw * FACTOR) / 100
    return round(flow_m3_h, 2)
