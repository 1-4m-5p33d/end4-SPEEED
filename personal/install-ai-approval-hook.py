#!/usr/bin/env python3
"""Add a persistent command approval toggle to the AI sidebar."""
import argparse
from pathlib import Path
import sys

MARKER = '// end4-personal command approval'

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected upstream code not found exactly once')
    return text.replace(old, new, 1)

def config(text):
    return replace_once(text, '            property JsonObject ai: JsonObject {\n                property string systemPrompt:', '            property JsonObject ai: JsonObject {\n                property bool confirmCommands: true // end4-personal command approval\n                property string systemPrompt:')

def sidebar(text):
    old='''                Item {
                    Layout.fillWidth: true
                }

                ButtonGroup {
                    // Command buttons'''
    new='''                RowLayout { // end4-personal command approval
                    spacing: 2
                    StyledText {
                        text: Config.options.ai.confirmCommands ? "Ask" : "Auto"
                        font.pixelSize: Appearance.font.pixelSize.small
                        color: Appearance.colors.colSubtext
                    }
                    Switch {
                        id: commandApprovalSwitch
                        checked: Config.options.ai.confirmCommands
                        onToggled: Config.options.ai.confirmCommands = checked
                        Accessible.name: "Ask before running AI commands"
                        StyledToolTip {
                            text: commandApprovalSwitch.checked ? "Ask before running AI commands in every chat" : "Automatic mode: AI commands run without asking in every chat"
                        }
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

                ButtonGroup {
                    // Command buttons'''
    return replace_once(text,old,new)

def service(text):
    text=replace_once(text,'''        property ApiStrategy currentStrategy

        function markDone()''','''        property ApiStrategy currentStrategy
        property var pendingFunctionCall: null // end4-personal command approval

        function markDone()''')
    text=replace_once(text,'''            requester.currentStrategy = root.currentApiStrategy;
            requester.currentStrategy.reset();''','''            requester.currentStrategy = root.currentApiStrategy;
            requester.pendingFunctionCall = null;
            requester.currentStrategy.reset();''')
    text=replace_once(text,'''                        requester.message.functionCall = result.functionCall;
                        root.handleFunctionCall(result.functionCall.name, result.functionCall.args, requester.message);''','''                        requester.message.functionCall = result.functionCall;
                        requester.pendingFunctionCall = result.functionCall;''')
    text=replace_once(text,'''            // end4-personal OpenAI tools: dispatch only after the process exits.
            if (result.functionCall) {
                requester.message.functionCall = result.functionCall;
                requester.message.functionName = result.functionCall.name;
                if (["get_shell_config", "run_shell_command"].includes(result.functionCall.name))
                    root.handleFunctionCall(result.functionCall.name, result.functionCall.args, requester.message);
                else
                    root.addFunctionOutputMessage(result.functionCall.name, "This function is not available for this model.");
            }

            // Handle error responses''','''            // end4-personal OpenAI tools: dispatch after the response process exits, for all API formats.
            const call = result.functionCall || requester.pendingFunctionCall;
            requester.pendingFunctionCall = null;
            if (call) {
                requester.message.functionCall = call;
                requester.message.functionName = call.name;
                const format = models[requester.message.model]?.api_format;
                if (format !== "openai" || ["get_shell_config", "run_shell_command"].includes(call.name))
                    root.handleFunctionCall(call.name, call.args, requester.message);
                else
                    root.addFunctionOutputMessage(call.name, "This function is not available for this model.");
            }

            // Handle error responses''')
    text=replace_once(text,'''            message.functionPending = true; // Use thinking to indicate the command is waiting for approval''','''            message.functionPending = true; // Use thinking to indicate the command is waiting for approval
            if (!Config.options.ai.confirmCommands) root.approveCommand(message);''')
    return text

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--dry-run',action='store_true'); parser.add_argument('directory',type=Path); args=parser.parse_args()
    paths=[args.directory/'modules/common/Config.qml',args.directory/'modules/ii/sidebarLeft/AiChat.qml',args.directory/'services/Ai.qml']
    changes=[]
    for path, transform in zip(paths,[config,sidebar,service]):
        text=path.read_text()
        if MARKER not in text: changes.append((path,transform(text)))
    for path,text in changes:
        if not args.dry_run: path.write_text(text)
        print(('Would update ' if args.dry_run else 'Updated ')+str(path))
    if not changes: print('AI command approval toggle already installed')

if __name__=='__main__':
    try: main()
    except (OSError,ValueError) as e: print('AI approval toggle:',e,file=sys.stderr); sys.exit(1)
