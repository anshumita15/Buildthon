# 🌙 SeizureDetector

Contactless under-mattress seizure detection and alerting system for nighttime monitoring.

## The Problem
~1 in 1000 people with epilepsy die of SUDEP (Sudden Unexpected Death in Epilepsy) each year. Most die alone, at night. Existing monitors cost $300+ and aren't accessible in low-resource settings.

## Our Solution
A Raspberry Pi + accelerometer (~$50 in parts) that:
- Detects tonic-clonic seizures via rhythmic mattress vibrations (3–6 Hz)
- Sounds a local buzzer + flashes red LED immediately
- Sends a free push notification to caretaker's phone via ntfy
- Escalates if no acknowledgement within 60 seconds
- Logs events to a real-time web dashboard

## Hardware
- Raspberry Pi 4
- GY-521 (MPU6050) accelerometer
- Piezo buzzer, 3x LEDs (red/yellow/green), push-button
- Jumper wires + breadboard

## Software
| File | Purpose |
|------|---------|
| `main.py` | Starts detector + dashboard together |
| `Detector.py` | FFT-based seizure detection (the brain) |
| `alerts.py` | Buzzer, LEDs, button, and ntfy push notification |
| `dashboard.py` | Flask web UI for live monitoring |
| `logger.py` | Records sensor data to CSV (setup only) |
| `analyze.py` | Computes stats on recorded CSV data (setup only) |
| `config.py` | Shared constants (pins, thresholds) |

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt --break-system-packages
```

### 2. Set up ntfy (free, no account needed)
- Download the **ntfy app** on the caretaker's phone (iOS or Android)
- Subscribe to topic: `SeizureDetectorTeam600`
- That's it — no credentials needed

### 3. Run the system
```bash
python3 main.py
```
This starts both the detector and dashboard in one command.

Or run them separately:
```bash
python3 Detector.py   # terminal 1
python3 dashboard.py  # terminal 2
```

### 4. View the dashboard
Open a browser on any laptop on the same network:
```
http://raspberrypi.local:5000
```

## Wiring
| Component | Pi Pin |
|-----------|--------|
| GY-521 VCC | Pin 1 (3.3V) |
| GY-521 GND | Pin 6 (GND) |
| GY-521 SDA | Pin 3 (GPIO2) |
| GY-521 SCL | Pin 5 (GPIO3) |
| Buzzer + | GPIO 17 (Pin 11) |
| Button | GPIO 27 (Pin 13) |
| Green LED | GPIO 22 (Pin 15) |
| Yellow LED | GPIO 23 (Pin 16) |
| Red LED | GPIO 24 (Pin 18) |

## Tuning
After wiring, run `Detector.py` and simulate a seizure by shaking the sensor at ~4 Hz. Watch the terminal output and adjust these two values in `Detector.py` until:
- Rhythmic shaking triggers alert within 10–15 seconds ✓
- Normal movement (rolling, tapping) does NOT trigger ✓

```python
rhythmic = ratio > 0.4        # increase if too many false alarms
strong   = amplitude > baseline_std * 5  # increase if too sensitive
```

## Built in 24 hours at Buildthon.