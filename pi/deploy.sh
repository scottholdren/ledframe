#!/usr/bin/env bash
# Push the working tree to the Pi and restart the service. The "flash" button.
#   pi/deploy.sh              # → ledframe.local
#   pi/deploy.sh 192.168.1.50
set -euo pipefail
HOST="${1:-ledframe.local}"
USER_="${LEDFRAME_USER:-scott}"
cd "$(dirname "$0")/.."
rsync -az --delete \
  --exclude .git --exclude node_modules --exclude '__pycache__' --exclude '*.pyc' \
  ./ "$USER_@$HOST:/opt/ledframe/src/"
ssh "$USER_@$HOST" 'sudo /opt/ledframe/venv/bin/pip install -q -r /opt/ledframe/src/pi/requirements.txt && sudo systemctl restart ledframe && sleep 1 && systemctl --no-pager --lines=8 status ledframe'
