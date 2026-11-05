#!/usr/bin/env bash
# Re-sync the curated live config into this repo's personal/ overlay.
#
# Run this after you change something in the UI (wallpaper, clock position, bar,
# keybinds, ...), then review and commit:
#   ./personal/capture.sh
#   git -C . diff
#   git add personal && git commit -m "personal: update config"
#
# Deliberately skipped: monitor layout, fontconfig, fish_variables, *.new,
# states.json, caches, .venv and unrelated app configs.

set -euo pipefail

PERSONAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="$PERSONAL_DIR/files"
WALL_DIR="$PERSONAL_DIR/wallpapers"

HYPR="$HOME/.config/hypr"
SHELL_CONF="$HOME/.config/illogical-impulse/config.json"

mkdir -p \
    "$FILES_DIR/.config/hypr/custom" \
    "$FILES_DIR/.config/hypr/hyprlock" \
    "$FILES_DIR/.config/illogical-impulse" \
    "$WALL_DIR"

for f in env execs general keybinds rules variables; do
    src="$HYPR/custom/$f.lua"
    [[ -f "$src" ]] && cp -f "$src" "$FILES_DIR/.config/hypr/custom/$f.lua"
done
for f in hyprlock.conf hyprlock/colors.conf; do
    src="$HYPR/$f"
    [[ -f "$src" ]] && cp -f "$src" "$FILES_DIR/.config/hypr/$f"
done

# Wallpaper + config.json (machine paths -> placeholders)
WALL="$(python3 -c "import json;print(json.load(open('$SHELL_CONF'))['background']['wallpaperPath'])" 2>/dev/null || true)"
if [[ -n "$WALL" && -f "$WALL" ]]; then
    cp -f "$WALL" "$WALL_DIR/$(basename "$WALL")"
    printf '%s' "$(basename "$WALL")" > "$WALL_DIR/.current"
fi

WALL="$WALL" SHELL_CONF="$SHELL_CONF" HOME_DIR="$HOME" PERSONAL_DIR="$PERSONAL_DIR" python3 - <<'PY'
import json, os

home = os.environ["HOME_DIR"]
wall = os.environ["WALL"]

def conv(o):
    if isinstance(o, dict):
        return {k: conv(v) for k, v in o.items()}
    if isinstance(o, list):
        return [conv(v) for v in o]
    if isinstance(o, str):
        if wall and o == wall:
            return "@WALLPAPER@"
        return o.replace(home, "@HOME@")
    return o

src = os.environ["SHELL_CONF"]
with open(src, encoding="utf-8") as f:
    data = json.load(f)
out = os.path.join(os.environ["PERSONAL_DIR"], "files/.config/illogical-impulse/config.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(conv(data), f, indent=4, ensure_ascii=False)
    f.write("\n")

# colors.conf also embeds the wallpaper path
cp = os.path.join(home, ".config/hypr/hyprlock/colors.conf")
dst = os.path.join(os.environ["PERSONAL_DIR"], "files/.config/hypr/hyprlock/colors.conf")
if os.path.isfile(cp):
    with open(cp, encoding="utf-8") as f:
        text = f.read()
    if wall:
        text = text.replace(wall, "@WALLPAPER@")
    text = text.replace(home, "@HOME@")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)

print("captured personal config")
PY

echo
echo "Now review and commit:"
echo "  git status"
echo "  git diff -- personal"
echo "  git add personal && git commit -m 'personal: update config'"