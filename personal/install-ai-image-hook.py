#!/usr/bin/env python3
"""Add image attachments to the installed OpenAI-compatible strategy."""
import argparse
from pathlib import Path
import sys

OLD = '''                ...messages.map(message => {
                    return {
                        "role": message.role,
                        "content": message.rawContent,
                    }
                }),'''
NEW = '''                ...messages.map((message, index) => {
                    const content = filePath && index === messages.length - 1 && message.role === "user"
                        ? [{ type: "text", text: message.rawContent },
                           { type: "image_url", image_url: { url: "data:{{ OPENAI_IMAGE_MIME }};base64,{{ OPENAI_IMAGE_DATA }}" } }]
                        : message.rawContent;
                    return { "role": message.role, "content": content };
                }),'''
HOOK = r'''
    // end4-personal: send a pending image as an OpenAI-compatible data URL.
    function buildScriptFileSetup(filePath) {
        const path = CF.FileUtils.trimFileProtocol(filePath);
        return `IMAGE_PATH='${CF.StringUtils.shellSingleQuoteEscape(path)}'\n`
            + 'IMAGE_MIME=$(file -b --mime-type "$IMAGE_PATH")\n'
            + 'case "$IMAGE_MIME" in image/jpeg|image/png|image/gif|image/webp) ;; *) printf "Unsupported image type; use PNG, JPEG, GIF, or WebP.\\n"; exit 1 ;; esac\n'
            + 'IMAGE_DATA=$(base64 -w 0 -- "$IMAGE_PATH") || exit 1\n';
    }

    function finalizeScriptContent(scriptContent: string): string {
        if (!scriptContent.includes("{{ OPENAI_IMAGE_DATA }}")) return scriptContent;
        const commandStart = scriptContent.lastIndexOf("curl --no-buffer ");
        const dataStart = scriptContent.indexOf(" --data '", commandStart);
        if (commandStart < 0 || dataStart < 0 || !scriptContent.endsWith("'\n"))
            throw new Error("Could not prepare image request");
        const setup = scriptContent.slice(0, commandStart);
        const curl = scriptContent.slice(commandStart, dataStart);
        let payload = scriptContent.slice(dataStart + " --data ".length, -1);
        payload = payload.replace("{{ OPENAI_IMAGE_MIME }}", `'"$IMAGE_MIME"'`)
                         .replace("{{ OPENAI_IMAGE_DATA }}", `'"$IMAGE_DATA"'`);
        return setup + "printf '%s' " + payload + " | " + curl + " --data-binary @-\n";
    }
'''

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    text = args.path.read_text()
    if '// end4-personal: send a pending image' in text:
        print('AI image integration already installed')
        return
    if text.count(OLD) != 1 or text.count('import QtQuick\n') != 1 or text.count('    function reset() {') != 1:
        raise ValueError('OpenAI strategy differs from the expected upstream layout')
    text = text.replace('import QtQuick\n', 'import QtQuick\nimport qs.modules.common.functions as CF\n', 1).replace(OLD, NEW, 1).replace('    function reset() {', HOOK + '\n    function reset() {', 1)
    if not args.dry_run:
        args.path.write_text(text)
    print(('Would install' if args.dry_run else 'Installed') + ' AI image integration')

if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f'AI image integration: {exc}', file=sys.stderr)
        sys.exit(1)
