import serial, time
import RPi.GPIO as GPIO

M0, M1 = 22, 27
GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
GPIO.setup(M0, GPIO.OUT); GPIO.setup(M1, GPIO.OUT)
GPIO.output(M0, 0); GPIO.output(M1, 1)
time.sleep(0.3)

s = serial.Serial("/dev/serial0", 9600, timeout=1)
s.reset_input_buffer()

cfg = bytes([0xC0, 0x00, 0x09,
             0x00, 0x00,  # address 0
             0x00,        # net id 0
             0x62,        # 9600 baud, 2400 airspeed
             0x00,        # 22dBm
             0x41,        # channel 65 = 915 MHz
             0x83,        # transparent mode (bit6=0), RSSI on
             0x00, 0x00])
s.write(cfg)
time.sleep(0.5)
resp = s.read(s.inWaiting())
print("Write response:", resp.hex())

# Read back to confirm
s.reset_input_buffer()
s.write(bytes([0xC1, 0x00, 0x09]))
resp = bytearray()
deadline = time.time() + 2.0
while len(resp) < 12 and time.time() < deadline:
    chunk = s.read(12 - len(resp))
    if chunk: resp += chunk
print(f"Readback: {resp.hex()}")
print(f"Reg9 should be 0x83: got {hex(resp[9]) if len(resp)==12 else '?'}")
s.close(); GPIO.cleanup()
