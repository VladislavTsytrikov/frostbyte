#!/bin/bash
set -e

G='\033[0;32m' D='\033[0;90m' B='\033[1m' N='\033[0m'

echo -e "\n${B}❄ FrostByte${N} installer\n"

# ── checks ──
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required" >&2; exit 1
fi

# ── source ──
if ! [ -f "$0" ]; then
    command -v curl &>/dev/null || { echo "Error: curl required" >&2; exit 1; }
    FB_TMP="$(mktemp -d)"; trap 'rm -rf "$FB_TMP"' EXIT
    RAW="https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main"
    echo -e "  ${D}downloading...${N}"
    curl -fsSL "$RAW/frostbyte"                -o "$FB_TMP/frostbyte"
    curl -fsSL "$RAW/frostbyte.service"        -o "$FB_TMP/frostbyte.service"
    mkdir -p "$FB_TMP/extension"
    curl -fsSL "$RAW/extension/metadata.json"  -o "$FB_TMP/extension/metadata.json"
    curl -fsSL "$RAW/extension/extension.js"   -o "$FB_TMP/extension/extension.js"
    DIR="$FB_TMP"
else
    DIR="$(cd "$(dirname "$0")" && pwd)"
fi

# ── install ──
mkdir -p ~/.local/bin
cp "$DIR/frostbyte" ~/.local/bin/frostbyte
chmod +x ~/.local/bin/frostbyte
echo -e "  ${G}✓${N} daemon    → ~/.local/bin/frostbyte"

EXT=~/.local/share/gnome-shell/extensions/frostbyte@cryogen
mkdir -p "$EXT"
cp "$DIR/extension/metadata.json" "$EXT/"
cp "$DIR/extension/extension.js"  "$EXT/"
echo -e "  ${G}✓${N} extension → frostbyte@cryogen"

mkdir -p ~/.config/systemd/user
cp "$DIR/frostbyte.service" ~/.config/systemd/user/
systemctl --user daemon-reload
echo -e "  ${G}✓${N} service   → frostbyte.service"

mkdir -p ~/.config/frostbyte

# ── activate ──
if command -v gnome-extensions &>/dev/null; then
    gnome-extensions enable frostbyte@cryogen 2>/dev/null \
        && echo -e "  ${G}✓${N} extension enabled" \
        || echo -e "  ${D}! extension installed — log out/in to activate${N}"
fi

systemctl --user enable --now frostbyte.service 2>/dev/null \
    && echo -e "  ${G}✓${N} daemon started" \
    || echo -e "  ${D}! run: systemctl --user enable --now frostbyte.service${N}"

if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "  ${D}! add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\"${N}"
fi

echo -e "\n${G}${B}Done!${N} FrostByte is running. ❄"
echo -e "${D}  config → ~/.config/frostbyte/config.json"
echo -e "  logs   → ~/.config/frostbyte/frostbyte.log"
echo -e "  tui    → frostbyte monitor${N}\n"
