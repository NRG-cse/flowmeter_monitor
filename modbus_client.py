from pymodbus.client import ModbusSerialClient
from config import PORT, BAUDRATE

def get_client():
    client = ModbusSerialClient(
        port=PORT,
        baudrate=BAUDRATE,
        parity='N',
        stopbits=1,
        bytesize=8,
        timeout=1
    )
    client.connect()
    return client
