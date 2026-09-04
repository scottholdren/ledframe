"""ledframe voice box — placeholder main loop.

Right now this only proves the box is alive: logs audio devices, opens the
serial link to the ESP32 if present, and heartbeats. The wake → STT → Claude
→ sandbox → serial pipeline lands here next.
"""
import logging
import os
import time

log = logging.getLogger("ledframe")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def audio_devices() -> None:
    try:
        import sounddevice as sd
        for i, d in enumerate(sd.query_devices()):
            if d["max_input_channels"] or d["max_output_channels"]:
                log.info("audio[%d] %s  in=%d out=%d", i, d["name"],
                         d["max_input_channels"], d["max_output_channels"])
    except Exception as e:  # noqa: BLE001
        log.warning("audio enumeration failed: %s", e)


def open_serial():
    port = os.environ.get("LEDFRAME_SERIAL", "/dev/ledframe-wall")
    if not os.path.exists(port):
        log.info("serial %s not present (ESP32 not plugged in?)", port)
        return None
    import serial
    ser = serial.Serial(port, 115200, timeout=0.1)
    log.info("serial open on %s", port)
    return ser


def main() -> None:
    log.info("ledframe voice box starting")
    log.info("anthropic key: %s", "set" if os.environ.get("ANTHROPIC_API_KEY") else "MISSING")
    log.info("deepgram key:  %s", "set" if os.environ.get("DEEPGRAM_API_KEY") else "MISSING")
    audio_devices()
    ser = open_serial()
    while True:
        time.sleep(60)
        log.info("heartbeat serial=%s", "up" if ser else "down")


if __name__ == "__main__":
    main()
