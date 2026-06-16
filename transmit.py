import serial, time
import RPi.GPIO as GPIO

M0, M1 = 22, 27
GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
GPIO.setup(M0, GPIO.OUT); GPIO.setup(M1, GPIO.OUT)
GPIO.output(M0, 0); GPIO.output(M1, 0)
time.sleep(0.5)

s = serial.Serial("/dev/serial0", 9600, timeout=1)
counter = 0
while True:
    msg = f"test{counter}\n".encode()
    s.write(msg)
    print(f"Sent: {msg}  - did TXD blink?")
    counter += 1
    time.sleep(3)
