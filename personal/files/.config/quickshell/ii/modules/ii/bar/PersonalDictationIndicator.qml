import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

Item {
    id: root
    Layout.alignment: Qt.AlignVCenter
    implicitHeight: 28
    implicitWidth: GlobalDictation.busy ? capsuleContents.implicitWidth + 25 : 0
    clip: true

    Behavior on implicitWidth {
        NumberAnimation { duration: 220; easing.type: Easing.OutCubic }
    }

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: 5
        radius: height / 2
        color: "#147bd1"
        opacity: GlobalDictation.busy ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 140 } }

        RowLayout {
            id: capsuleContents
            anchors.centerIn: parent
            spacing: 5

            MaterialSymbol {
                id: microphone
                text: GlobalDictation.recording ? "mic" : "hourglass_top"
                iconSize: 17
                color: "#ffffff"
                SequentialAnimation on opacity {
                    running: GlobalDictation.recording
                    loops: Animation.Infinite
                    NumberAnimation { from: 1; to: 0.5; duration: 600 }
                    NumberAnimation { from: 0.5; to: 1; duration: 600 }
                }
            }
            StyledText {
                text: GlobalDictation.recording ? "Recording" : "Transcribing"
                font.pixelSize: Appearance.font.pixelSize.small
                color: "#ffffff"
            }
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }
    StyledToolTip {
        text: GlobalDictation.recording ? "Recording — Super+Space to stop" : "Transcribing with Gemini"
        extraVisibleCondition: false
        alternativeVisibleCondition: hoverArea.containsMouse && GlobalDictation.busy
    }
}
