from mpu6050 import mpu6050
import numpy as np
from scipy.fft import rfft, rfftfreq
import time
import json
import os
from collections import deque
from alerts import trigger_alert
 
# ── constants ────────────────────────────────────────────────────────────────
sensor = mpu6050(0x68)
FS = 50
WINDOW_SEC = 4
WINDOW_SIZE = FS * WINDOW_SEC
BAND = (3, 6)               # Hz — typical seizure rhythm range
SEIZURE_CONFIRM_SEC = 10    # seconds of sustained rhythmic motion before alert
 
# shared state files (read by dashboard.py)
DATA_FILE   = "/tmp/seizureguard_data.json"
EVENTS_FILE = "/tmp/seizureguard_events.json"
 
# ── helpers ───────────────────────────────────────────────────────────────────
def write_data(magnitude: float, ratio: float, amplitude: float, status: str):
    """Write current sensor snapshot for the dashboard /data endpoint."""
    payload = {
        "timestamp": time.time(),
        "magnitude": round(magnitude, 4),
        "ratio":     round(ratio, 4),
        "amplitude": round(amplitude, 4),
        "status":    status,          # "ARMED" | "WARNING" | "SEIZURE"
    }
    with open(DATA_FILE, "w") as f:
        json.dump(payload, f)
 
 
def log_event(event_type: str, detail: str = ""):
    """Append a seizure-confirmation event to the events log."""
    events = []
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE) as f:
                events = json.load(f)
        except json.JSONDecodeError:
            events = []
 
    events.append({
        "time":   time.strftime("%H:%M:%S"),
        "type":   event_type,
        "detail": detail,
    })
 
    # keep the last 50 events so the file doesn't grow unbounded
    events = events[-50:]
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f)
 
 
# ── calibration ───────────────────────────────────────────────────────────────
print("Calibrating... keep bed empty for 10 seconds")
baseline_samples = []
for _ in range(FS * 10):
    a = sensor.get_accel_data()
    baseline_samples.append(np.sqrt(a["x"] ** 2 + a["y"] ** 2 + a["z"] ** 2))
    time.sleep(1 / FS)
 
baseline_std = np.std(baseline_samples)
print(f"Baseline noise std: {baseline_std:.3f}")
print("Monitoring...")
 
# write initial status so the dashboard has something to show immediately
write_data(9.8, 0.0, 0.0, "ARMED")
 
# ── main loop ─────────────────────────────────────────────────────────────────
buffer = deque(maxlen=WINDOW_SIZE)
seizure_seconds = 0
last_check = time.time()
 
while True:
    a = sensor.get_accel_data()
    mag = np.sqrt(a["x"] ** 2 + a["y"] ** 2 + a["z"] ** 2)
    buffer.append(mag)
 
    # analyse once per second when we have a full window
    if len(buffer) == WINDOW_SIZE and time.time() - last_check >= 1:
        last_check = time.time()
 
        signal    = np.array(buffer) - np.mean(buffer)
        freqs     = rfftfreq(len(signal), 1 / FS)
        power     = np.abs(rfft(signal)) ** 2
        band_mask = (freqs >= BAND[0]) & (freqs <= BAND[1])
 
        band_power  = power[band_mask].sum()
        total_power = power.sum() + 1e-9
        ratio       = band_power / total_power
        amplitude   = np.std(signal)
 
        rhythmic = ratio > 0.4
        strong   = amplitude > baseline_std * 5
 
        if rhythmic and strong:
            seizure_seconds += 1
            status = "WARNING" if seizure_seconds < SEIZURE_CONFIRM_SEC else "SEIZURE"
            print(f"⚠️  Possible seizure ({seizure_seconds}s) "
                  f"ratio={ratio:.2f} amp={amplitude:.2f}")
            write_data(mag, ratio, amplitude, status)
 
            if seizure_seconds >= SEIZURE_CONFIRM_SEC:
                print("🚨 SEIZURE CONFIRMED")
                log_event("SEIZURE CONFIRMED",
                          f"ratio={ratio:.2f} amp={amplitude:.2f}")
                trigger_alert()
                seizure_seconds = 0
 
        else:
            if seizure_seconds > 0:
                print(f"   ...cleared (ratio={ratio:.2f} amp={amplitude:.2f})")
                seizure_seconds = 0
            write_data(mag, ratio, amplitude, "ARMED")
 
    time.sleep(1 / FS)
