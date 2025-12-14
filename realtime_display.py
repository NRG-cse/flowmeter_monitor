import time
from flow_reader import read_flow
from config import READ_INTERVAL

print("🔵 Real-Time Flow Monitoring Started")

while True:
    flow = read_flow()
    if flow is not None:
        print(f"Flow Rate: {flow} m³/h")
    else:
        print("⚠️ Read Error")
    time.sleep(READ_INTERVAL)
