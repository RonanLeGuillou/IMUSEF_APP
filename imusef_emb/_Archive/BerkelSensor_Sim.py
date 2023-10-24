import RPi.GPIO as GPIO
import time

CH_A = 20
CH_Z = 16

global GPIO

GPIO.setmode(GPIO.BCM) 											# Broadcom pin-numbering scheme
GPIO.setwarnings(False)

# Setup System LED
GPIO.setup(CH_A, GPIO.OUT)
GPIO.output(CH_A, GPIO.LOW)

GPIO.setup(CH_Z, GPIO.OUT)
GPIO.output(CH_Z, GPIO.LOW)

RPM = 50

RPS = RPM / 60.0
pulses_per_second = RPS * 360

periode_time = 1/pulses_per_second


i = 0
while True:
    i = i + 1

    # Count upwards
    GPIO.output(CH_A, GPIO.HIGH)
    time.sleep(0.001)
    GPIO.output(CH_A, GPIO.LOW)

    # Reset
    if i >=360:
        i = 0
        print("CH_Z")
        GPIO.output(CH_Z, GPIO.HIGH)
        time.sleep(0.001)
        GPIO.output(CH_Z, GPIO.LOW)
        time.sleep(periode_time - 0.002)

    else:
        time.sleep(periode_time - 0.001)