from mpu6050 import mpu6050
import time, math

sensor = mpu6050(0x68)
print("Live sensor readings — move the sensor to see values change.")
print("Press Ctrl+C to stop.\n")

while True:
    d = sensor.get_accel_data()
    mag = math.sqrt(d['x']**2 + d['y']**2 + d['z']**2)
    bar = '█' * min(int(mag * 3), 50)
    print(f"X={d['x']:+6.2f}  Y={d['y']:+6.2f}  Z={d['z']:+6.2f}  |mag|={mag:5.2f}  {bar}", flush=True)
    time.sleep(0.1)
    