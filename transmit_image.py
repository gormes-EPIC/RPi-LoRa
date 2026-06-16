import serial, time, struct, zlib, base64
import RPi.GPIO as GPIO
from PIL import Image

img = Image.open("photo.jpg")
img.thumbnail((320, 240))
img.save("small.jpg", quality=40)

IMAGE = "small.jpg"
PAYLOAD = 50          # raw bytes per chunk (before base64)
PACKET_GAP = 0.5     # seconds between packets — tune if you drop data

M0, M1 = 22, 27
GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
GPIO.setup(M0, GPIO.OUT); GPIO.setup(M1, GPIO.OUT)
GPIO.output(M0, 0); GPIO.output(M1, 0)   # normal mode
time.sleep(0.5)

s = serial.Serial("/dev/serial0", 9600, timeout=1)

with open(IMAGE, "rb") as f:
    data = f.read()

chunks = [data[i:i+PAYLOAD] for i in range(0, len(data), PAYLOAD)]
total = len(chunks)
print(f"{len(data)} bytes -> {total} chunks")

# START frame: marker + total count
s.write(b"<START>" + struct.pack(">H", total) + b"\n")
time.sleep(PACKET_GAP)

for seq, chunk in enumerate(chunks):
    crc = zlib.crc32(chunk) & 0xFFFFFFFF
    raw = struct.pack(">HI", seq, crc) + chunk     # 2-byte seq, 4-byte crc, payload
    line = base64.b64encode(raw) + b"\n"           # text-safe, newline-terminated
    s.write(line)
    print(f"sent {seq+1}/{total}")
    time.sleep(PACKET_GAP)

s.write(b"<END>\n")
print("done")
