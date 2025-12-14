import csv, time
from datetime import datetime
from flow_reader import read_flow

with open("flow_log.csv", "a", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Time", "Flow (m3/h)"])

    while True:
        flow = read_flow()
        if flow:
            writer.writerow([datetime.now(), flow])
            print("Logged:", flow)
        time.sleep(1)
