#!/usr/bin/env bash
# ledframe Pi bootstrap — idempotent. Run once on a fresh Raspberry Pi OS Lite
# (64-bit, Bookworm or later), re-run any time to converge.
#
#   ssh ledframe.local 'curl -fsSL https://raw.githubusercontent.com/scottholdren/ledframe/main/pi/bootstrap.sh | sudo bash'
#
# or, after pi/deploy.sh has synced the repo:   sudo /opt/ledframe/src/pi/bootstrap.sh
set -euo pipefail

APP_USER="${SUDO_USER:-${APP_USER:-scott}}"
APP_DIR=/opt/ledframe
SRC="$APP_DIR/src"
VENV="$APP_DIR/venv"
ENV_FILE=/etc/ledframe.env
REPO=https://github.com/scottholdren/ledframe.git

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "run with sudo"; exit 1; }

log "apt packages"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  git rsync python3 python3-venv python3-dev python3-pip \
  portaudio19-dev libasound2-dev alsa-utils libsndfile1 \
  build-essential curl >/dev/null

log "user groups (serial + audio)"
usermod -aG dialout,audio,plugdev "$APP_USER"

log "source tree at $SRC"
mkdir -p "$APP_DIR"
if [ ! -d "$SRC/.git" ]; then
  git clone -q "$REPO" "$SRC"
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

log "python venv"
if [ ! -x "$VENV/bin/python" ]; then
  sudo -u "$APP_USER" python3 -m venv "$VENV"
fi
sudo -u "$APP_USER" "$VENV/bin/pip" install -q --upgrade pip
sudo -u "$APP_USER" "$VENV/bin/pip" install -q -r "$SRC/pi/requirements.txt"

log "secrets file $ENV_FILE"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'ENV'
# ledframe runtime secrets — never committed. chmod 600.
ANTHROPIC_API_KEY=
DEEPGRAM_API_KEY=
# Serial port to the ESP32-S3 (udev symlink from pi/99-ledframe.rules)
LEDFRAME_SERIAL=/dev/ledframe-wall
ENV
  chmod 600 "$ENV_FILE"
  echo "  created empty $ENV_FILE — fill in the API keys"
fi

log "udev rule: stable /dev/ledframe-wall for the ESP32-S3"
install -m 644 "$SRC/pi/99-ledframe.rules" /etc/udev/rules.d/99-ledframe.rules
udevadm control --reload-rules && udevadm trigger

log "systemd service"
sed "s|@APP_USER@|$APP_USER|g" "$SRC/pi/ledframe.service" > /etc/systemd/system/ledframe.service
systemctl daemon-reload
systemctl enable ledframe.service >/dev/null
systemctl restart ledframe.service

log "pi 5 usb current (only matters if NOT on a PD supply)"
CFG=/boot/firmware/config.txt
if grep -q 'Raspberry Pi 5' /proc/device-tree/model 2>/dev/null \
   && [ -f "$CFG" ] && ! grep -q '^usb_max_current_enable=1' "$CFG"; then
  echo 'usb_max_current_enable=1' >> "$CFG"
  echo "  added usb_max_current_enable=1 (takes effect next boot)"
fi

log "done"
systemctl --no-pager --lines=5 status ledframe.service || true
cat <<MSG

Next:
  1. sudo nano $ENV_FILE           # paste ANTHROPIC_API_KEY and DEEPGRAM_API_KEY
  2. sudo systemctl restart ledframe && journalctl -fu ledframe
  3. arecord -l                     # confirm the ReSpeaker shows up
  4. ls -l /dev/ledframe-wall       # confirm the S3 is seen (after it's plugged in)
  5. When everything works: sudo raspi-config → Performance → Overlay File System → enable
     (makes the SD card read-only; disable it again before running bootstrap/deploy)
MSG
