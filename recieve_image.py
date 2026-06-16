import serial, time, struct, zlib, base64
import RPi.GPIO as GPIO

M0, M1 = 22, 27
GPIO.setmode(GPIO.BCM); GPIO.setwarnings(False)
GPIO.setup(M0, GPIO.OUT); GPIO.setup(M1, GPIO.OUT)
GPIO.output(M0, 0); GPIO.output(M1, 0)
time.sleep(0.5)

s = serial.Serial("/dev/serial0", 9600, timeout=1)
s.reset_input_buffer()
with open("reciever.log", "a") as file:
    file.write(f"Starting {time.time()}...")
received = {}
total = None
buf = b""
counter = 1  # increments with each saved image

while True:
    buf += s.read(s.inWaiting() or 1)
    while b"\n" in buf:
        line, buf = buf.split(b"\n", 1)
        line = line.strip()
        if not line:
            continue

        if b"<START>" in line:
            idx = line.index(b"<START>")
            clean = line[idx:]
            try:
                total = struct.unpack(">H", clean[7:9])[0]
            except struct.error:
                print(f"[Image {counter}] malformed START: {line}")
                continue
            received = {}
            buf = b""
            print(f"[Image {counter}] START: expecting {total} chunks")
            continue

        if b"<END>" in line:
            if total is None:
                print("END received but never saw START — ignoring")
                continue
            missing = [i for i in range(total) if i not in received]
            if missing:
                print(f"[Image {counter}] INCOMPLETE — missing {len(missing)} chunks: {missing[:20]}")
            else:
                data = b"".join(received[i] for i in range(total))
                filename = f"~/RPi-LoRa/data/images/{time.time()}.jpg"
                with open(filename, "wb") as f:
                    f.write(data)
                print(f"[Image {counter}] SAVED {filename} ({len(data)} bytes)")
                counter += 1
            # Reset state for next image regardless of success
            received = {}
            total = None
            continue

        # Data packet
        try:
            raw = base64.b64decode(line)
            seq, crc = struct.unpack(">HI", raw[:6])
            chunk = raw[6:]
            if (zlib.crc32(chunk) & 0xFFFFFFFF) == crc:
                received[seq] = chunk
                print(f"[Image {counter}] chunk {seq + 1}/{total if total else '?'} ok")
            else:
                print(f"[Image {counter}] CRC fail seq {seq} — dropped")
        except Exception as e:
            print(f"[Image {counter}] bad packet: {e} | raw line: {line[:40]}")  # <-- add this
