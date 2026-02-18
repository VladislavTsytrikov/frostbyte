#!/bin/bash
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required" >&2
    exit 1
fi

echo "=== Installing FrostByte ==="

# daemon
echo "  Copying daemon to ~/.local/bin/frostbyte"
mkdir -p ~/.local/bin
cp "$DIR/frostbyte" ~/.local/bin/frostbyte
chmod +x ~/.local/bin/frostbyte

# gnome extension
EXT=~/.local/share/gnome-shell/extensions/frostbyte@cryogen
echo "  Installing GNOME extension to $EXT"
mkdir -p "$EXT"
cp "$DIR/extension/metadata.json" "$EXT/"
cp "$DIR/extension/extension.js" "$EXT/"

# systemd
echo "  Installing systemd user service"
mkdir -p ~/.config/systemd/user
cp "$DIR/frostbyte.service" ~/.config/systemd/user/
systemctl --user daemon-reload

# config
mkdir -p ~/.config/frostbyte

echo ""
echo "=== Done ==="
echo ""
echo "Step 1 — Enable GNOME extension (requires logout/login):"
echo "  gnome-extensions enable frostbyte@cryogen"
echo ""
echo "Step 2 — Start the daemon:"
echo "  systemctl --user enable --now frostbyte.service"
echo ""
echo "Commands:"
echo "  frostbyte status           — show frozen & candidate processes"
echo "  frostbyte thaw [name]      — thaw processes"
echo "  frostbyte freeze <name>    — manually freeze a process"
echo ""
echo "Config: ~/.config/frostbyte/config.json"
echo "Logs:   ~/.config/frostbyte/frostbyte.log"
echo ""
echo "To uninstall:"
echo "  systemctl --user disable --now frostbyte.service"
echo "  rm ~/.local/bin/frostbyte"
echo "  rm -rf ~/.local/share/gnome-shell/extensions/frostbyte@cryogen"
echo "  rm ~/.config/systemd/user/frostbyte.service"
