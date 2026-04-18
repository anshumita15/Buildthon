from mpu6050 import mpu6050
import time, csv, sys

sensor = mpu6050(0x68)
filename = sys.argv[1] if len(sys.argv) > 1 else "data.csv"
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30

print(f"Logging to {filename} for {duration} seconds...")
print("Starting in 3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
time.sleep(1)
print("GO!")

with open(filename, "w") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "x", "y", "z"])
    start = time.time()
    count = 0
    last_print = start
    while time.time() - start < duration:
        a = sensor.get_accel_data()
        writer.writerow([time.time(), a['x'], a['y'], a['z']])
        count += 1
        if time.time() - last_print >= 1:
            elapsed = int(time.time() - start)
            print(f"  {elapsed}s / {duration}s — {count} samples", flush=True)
            last_print = time.time()
        time.sleep(0.02)

print(f"Done! Logged {count} samples to {filename}")  