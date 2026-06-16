import serial, time, struct, zlib, base64
import RPi.GPIO as GPIO

OUTPUT = "received.jpg"

M0, M1 = 22, 27
GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
GPIO.setup(M0, GPIO.OUT); GPIO.setup(M1, GPIO.OUT)
GPIO.output(M0, 0); GPIO.output(M1, 0)
time.sleep(0.5)

s = serial.Serial("/dev/serial0", 9600, timeout=1)
s.reset_input_buffer()
print("Listening...")

received = {}     # seq -> chunk bytes
total = None
buf = b""

while True:
    buf += s.read(s.inWaiting() or 1)   # read whatever's available
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        line = line.strip()
        if not line:
            continue

        if line.startswith(b"<START>"):
            total = struct.unpack(">H", line[7:9])[0]
            received = {}
            print(f"START: expecting {total} chunks")
            continue

        if line.startswith(b"<END>"):
            if total is None:
                print("END but never saw START")
                continue
            missing = [i for i in range(total) if i not in received]
            if missing:
                print(f"INCOMPLETE — missing {len(missing)}: {missing[:20]}...")
            else:
                data = b"".join(received[i] for i in range(total))
                with open(OUTPUT, "wb") as f:
                    f.write(data)
                print(f"SAVED {OUTPUT} ({len(data)} bytes)")
            continue

        # data packet
        try:
            raw = base64.b64decode(line)
            seq, crc = struct.unpack(">HI", raw[:6])
            chunk = raw[6:]
            if (zlib.crc32(chunk) & 0xFFFFFFFF) == crc:
                received[seq] = chunk
                print(f"ok {seq+1}/{total if total else '?'}")
            else:
                print(f"CRC fail seq {seq} — dropped")
        except Exception as e:
            print(f"bad packet: {e}")
