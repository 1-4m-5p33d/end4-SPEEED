#!/usr/bin/env python3
"""Place the global dictation indicator in the installed top bar."""
import argparse
from pathlib import Path
import sys

MARKER = '// end4-personal global dictation'
OLD = '''                    property real realSpacing: 15
                    spacing: 0
'''
NEW = OLD + '''
                    PersonalDictationIndicator { // end4-personal global dictation
                    }
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    text = args.path.read_text()
    if MARKER in text:
        print('Global dictation bar indicator already installed')
        return
    if text.count(OLD) != 1:
        raise ValueError('Top bar does not match the expected upstream layout')
    if not args.dry_run:
        args.path.write_text(text.replace(OLD, NEW, 1))
    print(('Would install' if args.dry_run else 'Installed') + ' global dictation bar indicator')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print('Global dictation:', exc, file=sys.stderr)
        sys.exit(1)
