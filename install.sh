#!/bin/bash
set -e

G='\033[0;32m' D='\033[0;90m' B='\033[1m' C='\033[0;36m' N='\033[0m'

echo -e "\n  ${C}❄${N} ${B}FrostByte${N} installer\n"

# ── checks ──
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required" >&2; exit 1
fi

# ── download ──
RAW="https://raw.githubusercontent.com/VladislavTsytrikov/frostbyte/main"

if [ -f "$(dirname "$0")/frostbyte" ] && [ "$0" != "/dev/stdin" ] && [ "$0" != "bash" ]; then
    SRC="$(cd "$(dirname "$0")" && pwd)/frostbyte"
    echo -e "  ${D}using local ./frostbyte${N}"
else
    command -v curl &>/dev/null || { echo "Error: curl required" >&2; exit 1; }
    SRC="$(mktemp)"
    trap 'rm -f "$SRC"' EXIT
    echo -e "  ${D}downloading...${N}"
    curl -fsSL "$RAW/frostbyte" -o "$SRC"
fi

# ── install via built-in installer ──
python3 "$SRC" install

echo ""
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "  ${D}! add to PATH: export PATH=\"\$HOME/.local/bin:\$PATH\"${N}"
fi

echo -e "  ${D}config → ~/.config/frostbyte/config.json"
echo -e "  logs   → ~/.config/frostbyte/frostbyte.log"
echo -e "  tui    → frostbyte monitor${N}\n"
