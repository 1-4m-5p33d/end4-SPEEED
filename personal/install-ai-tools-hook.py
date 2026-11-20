#!/usr/bin/env python3
"""Enable approved OpenAI-compatible tool calls in the installed sidebar."""
import argparse
from pathlib import Path
import sys

MARKER = '// end4-personal OpenAI tools'

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected upstream code was not found exactly once')
    return text.replace(old, new, 1)

def strategy(text):
    text = replace_once(text, '    property bool isReasoning: false', '''    property bool isReasoning: false
    property var streamedToolCall: null // end4-personal OpenAI tools''')
    text = replace_once(text, '''                    const content = filePath && index === messages.length - 1 && message.role === "user"''', '''                    if (message.role === "assistant" && message.functionCall?.id) {
                        const call = message.functionCall;
                        return { role: "assistant", content: null, tool_calls: [{ id: call.id, type: "function", function: { name: call.name, arguments: JSON.stringify(call.args) } }] };
                    }
                    if (message.functionName && message.role === "user") {
                        const previous = messages[index - 1];
                        if (previous?.functionCall?.id)
                            return { role: "tool", tool_call_id: previous.functionCall.id, content: message.functionResponse || "" };
                    }
                    const content = filePath && index === messages.length - 1 && message.role === "user"''')
    text = replace_once(text, '            "tools": tools,', '''            "tools": tools.filter(tool => tool.function?.name !== "set_shell_config"),
            "parallel_tool_calls": false,''')
    text = replace_once(text, '''            let newContent = "";''', '''            // Assemble OpenAI streamed tool-call fragments before dispatching.
            for (const fragment of dataJson.choices?.[0]?.delta?.tool_calls ?? []) {
                if (fragment.index !== 0) continue;
                if (!streamedToolCall) streamedToolCall = { id: "", name: "", arguments: "" };
                if (fragment.id) streamedToolCall.id += fragment.id;
                if (fragment.function?.name) streamedToolCall.name += fragment.function.name;
                if (fragment.function?.arguments) streamedToolCall.arguments += fragment.function.arguments;
            }
            let newContent = "";''')
    text = replace_once(text, '''        // OpenAI format doesn't need special finish handling
        return {};''', '''        if (!streamedToolCall) return {};
        if (isReasoning) {
            message.content += "\n\n</think>\n\n";
            message.rawContent += "\n\n</think>\n\n";
            isReasoning = false;
        }
        const call = streamedToolCall;
        streamedToolCall = null;
        try {
            if (!call.id || !call.name) throw new Error("Incomplete tool call");
            return { functionCall: { id: call.id, name: call.name, args: JSON.parse(call.arguments || "{}") } };
        } catch (e) {
            message.content += "\\nCould not read the model's tool request: " + e;
            message.rawContent = message.content;
            return {};
        }''')
    return replace_once(text, '        isReasoning = false;\n    }\n\n}', '        isReasoning = false;\n        streamedToolCall = null;\n    }\n\n}')

def service(text):
    text = replace_once(text, '''            // Handle error responses
            if (requester.message.content.includes("API key not valid"))''', '''            // end4-personal OpenAI tools: dispatch only after the process exits.
            if (result.functionCall) {
                requester.message.functionCall = result.functionCall;
                requester.message.functionName = result.functionCall.name;
                if (["get_shell_config", "run_shell_command"].includes(result.functionCall.name))
                    root.handleFunctionCall(result.functionCall.name, result.functionCall.args, requester.message);
                else
                    root.addFunctionOutputMessage(result.functionCall.name, "This function is not available for this model.");
            }

            // Handle error responses
            if (requester.message.content.includes("API key not valid"))''')
    return replace_once(text, '        addFunctionOutputMessage(message.functionName, Translation.tr("Command rejected by user"))', '        addFunctionOutputMessage(message.functionName, Translation.tr("Command rejected by user"))\n        requester.makeRequest();')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('directory',type=Path); args=ap.parse_args()
    paths=[args.directory/'ai/OpenAiApiStrategy.qml',args.directory/'Ai.qml']
    changes=[]
    for path, transform in zip(paths,[strategy,service]):
        text=path.read_text()
        if MARKER not in text: changes.append((path,transform(text)))
    for path,text in changes:
        if not args.dry_run: path.write_text(text)
        print(('Would update ' if args.dry_run else 'Updated ')+str(path))
    if not changes: print('AI tools integration already installed')

if __name__ == '__main__':
    try: main()
    except (OSError,ValueError) as exc: print('AI tools integration:',exc,file=sys.stderr); sys.exit(1)
