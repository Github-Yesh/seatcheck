#!/bin/bash
set -euo pipefail
# WHY: the phone cannot use this Mac's loopback address, so listen on the local network.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
INTERFACE="${1:-en0}"
LAN_IP="$(ipconfig getifaddr "$INTERFACE" 2>/dev/null || true)"
if [[ -z "$LAN_IP" ]]; then
  echo "No IPv4 address on $INTERFACE. Join Wi-Fi, or pass the connected interface: $0 en1" >&2
  exit 1
fi
printf 'SeatCheck: http://%s:8765\nLabeling:  http://%s:8765/?label=1\n' "$LAN_IP" "$LAN_IP"
if lsof -nP -iTCP:8765 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8765 is already in use. Check the URLs above; stop the old server in its own terminal before restarting." >&2
  exit 1
fi
if [[ ! -x .venv/app/bin/python ]]; then
  echo "Missing .venv/app/bin/python; use the existing app environment in app/README.md." >&2
  exit 1
fi
echo "Keep this terminal open and the Mac awake. Suggestions stay off. Ctrl-C stops this server."
exec .venv/app/bin/python -m app.server --host 0.0.0.0 --port 8765
