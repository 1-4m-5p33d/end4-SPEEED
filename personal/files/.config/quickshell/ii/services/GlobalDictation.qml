pragma Singleton
pragma ComponentBehavior: Bound

import qs.services
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import QtQuick

Singleton {
    id: root
    property bool recording: false
    property bool transcribing: false
    readonly property bool busy: recording || transcribing
    property var targetWindow: null
    property string resultText: ""
    property string resultError: ""

    Component.onCompleted: {
        if (!KeyringStorage.loaded) KeyringStorage.fetchKeyringData();
    }

    function showError(message) {
        Quickshell.execDetached(["notify-send", "-u", "normal", "Voice typing", message]);
    }

    function toggle() {
        if (recording) {
            stop();
            return;
        }
        if (transcribing || typing.running) {
            showError("Voice typing is still finishing. Please wait.");
            return;
        }
        if (!Ai.apiKeysLoaded) {
            KeyringStorage.fetchKeyringData();
            showError("Loading your saved Gemini key. Try again in a moment.");
            return;
        }
        const key = Ai.apiKeys?.gemini ?? "";
        if (!key) {
            showError("Set your Gemini API key in the AI sidebar with /key first.");
            return;
        }
        if (!ToplevelManager.activeToplevel) {
            showError("Focus an application window and a text field first.");
            return;
        }
        targetWindow = ToplevelManager.activeToplevel;
        resultText = "";
        resultError = "";
        recorder.environment = {"GEMINI_API_KEY": key};
        recording = true;
        recorder.running = true;
        recordingLimit.restart();
    }

    function stop() {
        if (!recording) return;
        recording = false;
        transcribing = true;
        recordingLimit.stop();
        recorder.write("stop\n");
    }

    GlobalShortcut {
        name: "personalDictationToggle"
        description: "Start or stop global voice typing"
        onPressed: root.toggle()
    }

    Timer {
        id: recordingLimit
        interval: 59000
        repeat: false
        onTriggered: root.stop()
    }

    Process {
        id: recorder
        stdinEnabled: true
        command: ["python3", `${Quickshell.env("HOME")}/.local/share/end4-personal/voice-typing.py`]
        stdout: SplitParser {
            onRead: line => {
                try {
                    const result = JSON.parse(line);
                    root.resultText = result.text ?? "";
                    root.resultError = result.error ?? "";
                } catch (e) {
                    root.resultError = "Could not read the transcription response.";
                }
            }
        }
        onExited: (exitCode, exitStatus) => {
            recordingLimit.stop();
            root.recording = false;
            root.transcribing = false;
            if (exitCode !== 0 || root.resultError.length > 0 || root.resultText.length === 0) {
                root.showError(root.resultError || "Voice typing failed. Check your microphone and Gemini API key.");
                return;
            }
            if (!root.targetWindow || ToplevelManager.activeToplevel !== root.targetWindow) {
                root.showError("The active window changed. The transcription was not typed; try again in the intended window.");
                return;
            }
            // Avoid triggering Enter or Tab shortcuts in terminals and other applications.
            const safeText = root.resultText.replace(/[\r\n\t]+/g, " ");
            typing.command = ["wtype", "--", safeText];
            typing.running = true;
        }
    }

    Process {
        id: typing
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) root.showError("Could not type the transcription. Check that wtype and Wayland virtual keyboard support are available.");
        }
    }
}
