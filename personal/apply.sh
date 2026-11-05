#!/usr/bin/env bash
# Apply this repo's personal overlay on top of an installed end-4 / illogical-impulse setup.
#
# Usage:
#   ./personal/apply.sh            # apply
#   ./personal/apply.sh --dry-run  # show what would change
#
# It installs:
#   - ~/.config/hypr/custom/*.lua        (Hyprland user layer; survives ./setup install)
#   - ~/.config/hypr/hyprlock.conf       (12-hour clock)
#   - ~/.config/hypr/hyprlock/colors.conf
#   - ~/.config/illogical-impulse/config.json  (wallpaper, clock position, bar, ...)
#   - the wallpaper image into your XDG Pictures dir
#
# It deliberately does NOT touch:
#   - monitor layout (monitors.lua / workspaces.conf)  -> machine specific
#   - fontconfig (keeps the repo's default fonts)
#   - unrelated app configs, caches, .venv, states.json

set -euo pipefail

PERSONAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$PERSONAL_DIR/.." && pwd)"
FILES_DIR="$PERSONAL_DIR/files"
WALL_DIR="$PERSONAL_DIR/wallpapers"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

say() { printf '%s\n' "$*"; }
run() { if $DRY_RUN; then say "[dry-run] $*"; else "$@"; fi; }

if [[ ! -d "$HOME/.config/hypr/custom" ]]; then
    say "warning: ~/.config/hypr/custom not found."
    say "         Run './setup install' from this repo first."
fi

# --- Wallpaper target -------------------------------------------------------
PICS="$(xdg-user-dir PICTURES 2>/dev/null || true)"
if [[ -z "${PICS:-}" || "$PICS" == "$HOME" ]]; then
    PICS="$HOME/Pictures"
fi

WALL_NAME="$(cat "$WALL_DIR/.current" 2>/dev/null || true)"
if [[ -z "$WALL_NAME" ]]; then
    WALL_NAME="$(find "$WALL_DIR" -maxdepth 1 -type f ! -name '.current' -printf '%f\n' 2>/dev/null | head -n1)"
fi
WALL_SRC="$WALL_DIR/$WALL_NAME"
WALL_DST="$PICS/$WALL_NAME"

if [[ -n "$WALL_NAME" && -f "$WALL_SRC" ]]; then
    run mkdir -p "$PICS"
    run cp -f "$WALL_SRC" "$WALL_DST"
    say "wallpaper -> $WALL_DST"
else
    say "warning: no wallpaper found in $WALL_DIR; config will keep its placeholder."
    WALL_DST="@WALLPAPER@"
fi

# --- Curated config files ---------------------------------------------------
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/end4-personal/backups/$STAMP"

if $DRY_RUN; then
    say "[dry-run] would install files from $FILES_DIR into $HOME"
else
    FILES_DIR="$FILES_DIR" HOME_DIR="$HOME" WALL_DST="$WALL_DST" BACKUP_DIR="$BACKUP_DIR" python3 - <<'PY'
import os, shutil

files_dir = os.environ["FILES_DIR"]
home = os.environ["HOME_DIR"]
wall = os.environ["WALL_DST"]
backup_dir = os.environ["BACKUP_DIR"]

for root, _dirs, names in os.walk(files_dir):
    for name in names:
        src = os.path.join(root, name)
        rel = os.path.relpath(src, files_dir)
        dst = os.path.join(home, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if os.path.isfile(dst):
            b = os.path.join(backup_dir, rel)
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(dst, b)

        with open(src, encoding="utf-8") as f:
            text = f.read()
        text = text.replace("@HOME@", home).replace("@WALLPAPER@", wall)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(text)
        print("installed", rel)
PY
fi

# --- Fix known-invalid upstream values --------------------------------------
# Upstream sets decoration.shadow.render_power = 10, but Hyprland rejects
# anything above 4 and reports a config error on every reload. Patch the
# installed file (not tracked in this repo) instead of overwriting it.
GEN="$HOME/.config/hypr/hyprland/general.lua"
if [[ -f "$GEN" ]] && grep -q 'render_power = 10' "$GEN"; then
    run sed -i 's/render_power = 10/render_power = 4/' "$GEN"
    say "patched upstream render_power 10 -> 4 in $GEN"
fi

# --- Reload / regenerate ----------------------------------------------------
if command -v hyprctl >/dev/null 2>&1 && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    run hyprctl reload >/dev/null || true
fi

SWITCHWALL="$HOME/.config/quickshell/ii/scripts/colors/switchwall.sh"
if [[ -f "$SWITCHWALL" && -f "$WALL_DST" ]] \
        && command -v hyprctl >/dev/null 2>&1 \
        && [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]]; then
    say "regenerating wallpaper-derived colors (matugen)..."
    run bash "$SWITCHWALL" --image "$WALL_DST" || say "warning: switchwall.sh failed; run it manually."
else
    say "note: start Hyprland, then run:"
    say "      $SWITCHWALL --image \"$WALL_DST\""
fi

if [[ -d "$BACKUP_DIR" ]]; then
    say "backup of overwritten files: $BACKUP_DIR"
fi

say ""
say "Done."
say "Monitor layout is not tracked on purpose; set it on this machine with nwg-displays or 'hyprctl monitors'."