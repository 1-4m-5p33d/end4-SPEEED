#!/usr/bin/env python3
"""Place the global dictation indicator beside the top-left bar icon."""
import argparse
from pathlib import Path
import sys

MARKER = '// end4-personal global dictation left'
OLD_INDICATOR = '''
                    PersonalDictationIndicator { // end4-personal global dictation
                    }
'''
ANCHOR = '''            ActiveWindow {
'''
INSERT = '''            PersonalDictationIndicator { // end4-personal global dictation left
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
    if OLD_INDICATOR in text:
        if text.count(OLD_INDICATOR) != 1:
            raise ValueError('Found multiple old dictation indicators')
        text = text.replace(OLD_INDICATOR, '', 1)
    if text.count(ANCHOR) != 1 or '// end4-personal global dictation' in text:
        raise ValueError('Top bar does not match the expected upstream layout')
    if not args.dry_run:
        args.path.write_text(text.replace(ANCHOR, INSERT + ANCHOR, 1))
    print(('Would install' if args.dry_run else 'Installed') + ' global dictation bar indicator')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print('Global dictation:', exc, file=sys.stderr)
        sys.exit(1)
