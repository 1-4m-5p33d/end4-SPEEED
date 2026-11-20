import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

Item {
    id: root
    implicitWidth: 20
    implicitHeight: 22
    Layout.alignment: Qt.AlignVCenter
    Layout.rightMargin: 10

    MaterialSymbol {
        id: microphone
        anchors.centerIn: parent
        text: GlobalDictation.transcribing ? "hourglass_top" : "mic"
        iconSize: 19
        color: "#67b7ff"
        opacity: GlobalDictation.busy ? 1 : 0.55
        SequentialAnimation on opacity {
            running: GlobalDictation.recording
            loops: Animation.Infinite
            NumberAnimation { from: 1; to: 0.3; duration: 600 }
            NumberAnimation { from: 0.3; to: 1; duration: 600 }
        }
    }
    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }
    StyledToolTip {
        text: GlobalDictation.recording ? "Recording — Super+Space to stop" : (GlobalDictation.transcribing ? "Transcribing with Gemini" : "Voice typing — Super+Space")
        extraVisibleCondition: false
        alternativeVisibleCondition: hoverArea.containsMouse
    }
}
