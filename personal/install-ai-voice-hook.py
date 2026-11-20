#!/usr/bin/env python3
"""Add a microphone button to the installed sidebar."""
import argparse
from pathlib import Path
import sys

MARKER = '// end4-personal voice typing'
PROCESS = '''    // end4-personal voice typing
    property bool voiceRecording: false
    property bool voiceProcessing: false

    Process {
        id: voiceTypingProcess
        stdinEnabled: true
        command: ["python3", `${Quickshell.env("HOME")}/.local/share/end4-personal/voice-typing.py`]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const result = JSON.parse(text);
                    if (result.error) {
                        Ai.addMessage(result.error, Ai.interfaceRole);
                    } else if (result.text) {
                        const separator = messageInputField.text.length && !/\\s$/.test(messageInputField.text) ? " " : "";
                        messageInputField.text += separator + result.text;
                        messageInputField.forceActiveFocus();
                    }
                } catch (e) {
                    Ai.addMessage("Voice typing failed. Check the microphone and try again.", Ai.interfaceRole);
                }
            }
        }
        onExited: (exitCode, exitStatus) => {
            root.voiceRecording = false;
            root.voiceProcessing = false;
        }
    }

'''
BUTTON = '''                RippleButton { // end4-personal voice typing
                    id: voiceButton
                    Layout.alignment: Qt.AlignBottom
                    implicitWidth: 40
                    implicitHeight: 40
                    buttonRadius: Appearance.rounding.small
                    enabled: !root.voiceProcessing
                    toggled: root.voiceRecording

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: voiceButton.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: {
                            if (root.voiceRecording) {
                                root.voiceRecording = false;
                                root.voiceProcessing = true;
                                voiceTypingProcess.write("stop\\n");
                            } else {
                                const key = Ai.apiKeys?.gemini ?? "";
                                if (!key) {
                                    Ai.addMessage("Voice typing needs a Gemini API key. Select a Gemini model and use /key first.", Ai.interfaceRole);
                                    return;
                                }
                                voiceTypingProcess.environment = { "GEMINI_API_KEY": key };
                                root.voiceRecording = true;
                                voiceTypingProcess.running = true;
                            }
                        }
                    }
                    contentItem: MaterialSymbol {
                        anchors.centerIn: parent
                        horizontalAlignment: Text.AlignHCenter
                        iconSize: 22
                        color: root.voiceRecording ? Appearance.m3colors.m3onPrimary : Appearance.colors.colOnLayer2
                        text: root.voiceRecording ? "stop" : (root.voiceProcessing ? "hourglass_top" : "mic")
                    }
                    StyledToolTip {
                        text: root.voiceRecording ? "Stop recording and transcribe" : (root.voiceProcessing ? "Transcribing…" : "Voice typing (audio sent to Gemini)")
                    }
                }
'''

def main():
    p=argparse.ArgumentParser(); p.add_argument('--dry-run',action='store_true'); p.add_argument('path',type=Path); a=p.parse_args()
    text=a.path.read_text()
    if MARKER in text:
        print('AI voice typing already installed'); return
    process='    Process {\n        id: decodeImageAndAttachProc'
    button='                RippleButton { // Send button'
    if text.count(process)!=1 or text.count(button)!=1:
        raise ValueError('Sidebar does not match the expected upstream layout')
    text=text.replace(process,PROCESS+process,1).replace(button,BUTTON+button,1)
    if not a.dry_run: a.path.write_text(text)
    print(('Would install' if a.dry_run else 'Installed')+' AI voice typing')
if __name__=='__main__':
    try: main()
    except (OSError,ValueError) as e: print('AI voice typing:',e,file=sys.stderr); sys.exit(1)
