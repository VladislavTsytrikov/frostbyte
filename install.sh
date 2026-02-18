#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing Freezer ==="

# daemon
echo "  Copying daemon to ~/.local/bin/freezer"
mkdir -p ~/.local/bin
cp "$DIR/freezer" ~/.local/bin/freezer
chmod +x ~/.local/bin/freezer

# gnome extension
EXT=~/.local/share/gnome-shell/extensions/freezer@cryogen
echo "  Installing GNOME extension to $EXT"
mkdir -p "$EXT"
cp "$DIR/extension/metadata.json" "$EXT/"
cp "$DIR/extension/extension.js" "$EXT/"

# systemd
echo "  Installing systemd user service"
mkdir -p ~/.config/systemd/user
cp "$DIR/freezer.service" ~/.config/systemd/user/
systemctl --user daemon-reload

# config
mkdir -p ~/.config/freezer

echo ""
echo "=== Done ==="
echo ""
echo "Step 1 — Enable GNOME extension (requires logout/login):"
echo "  gnome-extensions enable freezer@cryogen"
echo ""
echo "Step 2 — Start the daemon:"
echo "  systemctl --user enable --now freezer.service"
echo ""
echo "Commands:"
echo "  freezer status           — show frozen & candidate processes"
echo "  freezer thaw [name]      — thaw processes"
echo "  freezer freeze <name>    — manually freeze a process"
echo ""
echo "Config: ~/.config/freezer/config.json"
echo "Logs:   ~/.config/freezer/freezer.log"
