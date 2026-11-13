#!/usr/bin/env python3
"""Apply the personal lyrics integration to an installed upstream shell."""
import argparse
import os
from pathlib import Path
import sys

MARKER = "// end4-personal lyrics"
PLAYER_OLD = """        RowLayout {
            anchors.fill: parent
            anchors.margins: 13
            spacing: 15

            Rectangle { // Art background"""
PLAYER_NEW = """        PersonalLyrics { // end4-personal lyrics
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            anchors.bottomMargin: 12
            height: 104
            player: root.player
            textColor: blendedColors.colOnLayer0
            mutedColor: blendedColors.colSubtext
        }

        RowLayout {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: parent.height - 142
            anchors.margins: 13
            spacing: 15

            Rectangle { // Art background"""
CONTROLS_OLD = "                        implicitHeight: root.widgetHeight\n"
CONTROLS_NEW = "                        implicitHeight: root.widgetHeight + 116 // end4-personal lyrics\n"


def transform(path, old, new):
    content = path.read_text(encoding="utf-8")
    if content.count(MARKER) == 1 and new in content:
        return None
    if MARKER in content or content.count(old) != 1:
        raise ValueError(f"{path}: expected upstream insertion point not found or hook modified")
    return content.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    changes = []
    try:
        for name, old, new in (("PlayerControl.qml", PLAYER_OLD, PLAYER_NEW),
                               ("MediaControls.qml", CONTROLS_OLD, CONTROLS_NEW)):
            path = args.directory / name
            changes.append((path, transform(path, old, new)))
    except (OSError, ValueError) as exc:
        print(f"lyrics hook not installed: {exc}", file=sys.stderr)
        return 1
    for path, content in changes:
        if content is None:
            print(f"lyrics hook already installed: {path}")
        elif args.dry_run:
            print(f"[dry-run] would add lyrics hook: {path}")
        else:
            temporary = path.with_name(path.name + ".personal-tmp")
            try:
                temporary.write_text(content, encoding="utf-8")
                os.chmod(temporary, path.stat().st_mode)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
            print(f"installed lyrics hook: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
