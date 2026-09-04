# The Pi as firmware

The voice box is a Raspberry Pi 5, but it's treated like a microcontroller:
nothing on it is configured by hand, and starting over is a five-minute
mechanical procedure. Everything the box *is* lives in this directory.

| File | Role |
|---|---|
| `bootstrap.sh` | Run once on a fresh card (idempotent). Installs packages, venv, service, udev rule, secrets file. |
| `deploy.sh` | The "flash" button. rsyncs the working tree to the Pi and restarts the service. |
| `ledframe.service` | systemd unit: runs `python -m voice` as your user, restarts on crash. |
| `99-ledframe.rules` | udev rule so the ESP32-S3 is always `/dev/ledframe-wall`, whichever port it enumerates on. |
| `requirements.txt` | Python deps for the venv at `/opt/ledframe/venv`. |

Secrets (`ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY`) live only in
`/etc/ledframe.env` on the Pi, created empty by bootstrap.

## Flash a card (Mac)

1. Open **Raspberry Pi Imager** (`brew install --cask raspberry-pi-imager`).
2. Device: Raspberry Pi 5. OS: **Raspberry Pi OS Lite (64-bit)**. Storage: the card.
3. Click **Edit Settings** before writing, and set:
   - Hostname `ledframe`
   - Username `scott`, a password
   - Wi-Fi SSID/password, country `US`
   - Services tab: **Enable SSH → Allow public-key authentication only**, paste
     the contents of `~/.ssh/id_ed25519_oss.pub`
   Imager remembers these, so the second card is just "Write".
4. Write. Move the card to the Pi, power it, wait ~90 s.

## First boot

```sh
ssh scott@ledframe.local
curl -fsSL https://raw.githubusercontent.com/scottholdren/ledframe/main/pi/bootstrap.sh | sudo bash
sudo nano /etc/ledframe.env        # paste the two API keys
sudo systemctl restart ledframe
journalctl -fu ledframe            # should list audio devices and heartbeat
```

## Day to day

```sh
pi/deploy.sh                       # push code + restart
ssh scott@ledframe.local journalctl -fu ledframe
```

## Make it bulletproof (once it's in the frame)

`sudo raspi-config` → Performance Options → Overlay File System → enable.
The root filesystem becomes read-only in RAM; pulling the plug can't corrupt
the card. To update code, disable the overlay, reboot, deploy, re-enable.
Keep a second card flashed and bootstrapped in the frame's back pocket.

## Recovery

Swap in the spare card. Or: Imager → Write (settings remembered) → first
boot steps above. There is nothing else to restore; the animation library
is the one thing worth backing up (`/opt/ledframe/library/`, once it exists).

## Power

The Pi 5 caps USB ports at 600 mA unless it sees a 5 A PD supply. The
ReSpeaker with a speaker attached can exceed that. Use the official 27 W
supply on its own cord. Bootstrap also sets `usb_max_current_enable=1` as a
belt-and-braces measure for a non-PD 5 V tap.
