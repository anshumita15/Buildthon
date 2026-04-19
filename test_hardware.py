import RPi.GPIO as GPIO
import time

BUZZER = 17
BTN    = 27
GREEN, YELLOW, RED = 22, 23, 24

GPIO.setmode(GPIO.BCM)
GPIO.setup([BUZZER, GREEN, YELLOW, RED], GPIO.OUT)
GPIO.setup(BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("Testing GREEN LED...")
GPIO.output(GREEN, True); time.sleep(1); GPIO.output(GREEN, False)

print("Testing YELLOW LED...")
GPIO.output(YELLOW, True); time.sleep(1); GPIO.output(YELLOW, False)

print("Testing RED LED...")
GPIO.output(RED, True); time.sleep(1); GPIO.output(RED, False)

print("Testing BUZZER (3 seconds)...")
GPIO.output(BUZZER, True); time.sleep(3); GPIO.output(BUZZER, False)

print("Press the acknowledge button within 10 seconds...")
start = time.time()
while time.time() - start < 10:
    if GPIO.input(BTN) == GPIO.LOW:
        print("✅ Button press detected!")
        break
    time.sleep(0.1)
else:
    print("❌ No button press detected")

GPIO.cleanup()
print("Test complete.")