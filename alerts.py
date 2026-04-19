import requests
import RPi.GPIO as GPIO
import time
 
# ── ntfy config ───────────────────────────────────────────────────────────────
# Change this to any unique topic name you make up — caretaker subscribes to same name in ntfy app
NTFY_TOPIC = "SeizureDetectorTeam600"
NTFY_URL   = f"https://ntfy.sh/{NTFY_TOPIC}"
 
# ── GPIO pin config ───────────────────────────────────────────────────────────
BUZZER = 17
BTN    = 27
GREEN, YELLOW, RED = 22, 23, 24
 
GPIO.setmode(GPIO.BCM)
GPIO.setup([BUZZER, GREEN, YELLOW, RED], GPIO.OUT)
GPIO.setup(BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
 
# ── helpers ───────────────────────────────────────────────────────────────────
def send_alert(message: str, priority: str = "urgent"):
    """Send a push notification via ntfy.sh — free, no account needed."""
    try:
        requests.post(
            NTFY_URL,
            data=message,
            headers={
                "Title":    "Seizure detector",
                "Priority": priority,
                "Tags":     "rotating_light",
            },
            timeout=5,
        )
    except requests.exceptions.RequestException:
        # if internet is down, don't crash — buzzer still fires
        print("⚠️  ntfy notification failed (no internet?), buzzer still active")
 
 
# ── main alert function (called by detector.py) ───────────────────────────────
def trigger_alert():
    # fire buzzer + red LED immediately
    GPIO.output(RED,    True)
    GPIO.output(BUZZER, True)
 
    # send push notification to caretaker's phone
    send_alert("🚨 Seizure detected. Check immediately.")
 
    # wait up to 60 seconds for caretaker to press the button
    start = time.time()
    while time.time() - start < 60:
        if GPIO.input(BTN) == GPIO.LOW:
            # button pressed — silence everything
            GPIO.output(RED,    False)
            GPIO.output(BUZZER, False)
            GPIO.output(GREEN,  True)   # green = acknowledged
            send_alert("✅ Alert acknowledged.", priority="low")
            return
        time.sleep(0.1)
 
    # no acknowledgment after 60s — send escalation notification
    send_alert("⚠️ No acknowledgment after 60 seconds. Check immediately.", priority="urgent")
    GPIO.output(BUZZER, False)
 