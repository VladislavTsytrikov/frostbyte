#!/bin/bash
set -e

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required" >&2
    exit 1
fi

# Detect if running via curl|bash (no local script file)
if ! [ -f "$0" ]; then
    if ! command -v curl &>/dev/null; then
        echo "Error: curl is required for remote install" >&2
        exit 1
    fi
    FB_TMP="$(mktemp -d)"
    trap 'rm -rf "$FB_TMP"' EXIT
    RAWBASE="https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main"
    echo "  Downloading FrostByte files..."
    curl -fsSL "$RAWBASE/frostbyte"                -o "$FB_TMP/frostbyte"
    curl -fsSL "$RAWBASE/frostbyte.service"        -o "$FB_TMP/frostbyte.service"
    mkdir -p "$FB_TMP/extension"
    curl -fsSL "$RAWBASE/extension/metadata.json"  -o "$FB_TMP/extension/metadata.json"
    curl -fsSL "$RAWBASE/extension/extension.js"   -o "$FB_TMP/extension/extension.js"
    DIR="$FB_TMP"
else
    DIR="$(cd "$(dirname "$0")" && pwd)"
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
echo "  frostbyte monitor          — live TUI dashboard"
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
