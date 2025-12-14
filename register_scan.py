from modbus_client import get_client

client = get_client()

for addr in range(0, 50):
    res = client.read_holding_registers(addr, 1, slave=1)
    if not res.isError():
        print(f"Register {addr} → {res.registers}")
