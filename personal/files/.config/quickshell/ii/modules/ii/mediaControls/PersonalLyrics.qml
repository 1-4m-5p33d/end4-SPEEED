pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Quickshell.Services.Mpris
import qs.modules.common
import "PersonalLyrics.js" as Lyrics

Item {
    id: root
    required property MprisPlayer player
    required property color textColor
    required property color mutedColor
    property var lines: []
    property string status: "Looking for lyrics…"
    property int generation: 0
    property var request: null
    readonly property string trackKey: JSON.stringify([player?.trackTitle || "", player?.trackArtist || "", player?.trackAlbum || "", player?.length || 0])
    readonly property int currentLine: Lyrics.currentIndex(lines, player?.position ?? 0)
    implicitHeight: lyricColumn.implicitHeight

    onTrackKeyChanged: scheduleLookup()
    Component.onCompleted: scheduleLookup()
    Component.onDestruction: {
        generation++;
        if (request) request.abort();
    }

    function scheduleLookup() {
        generation++;
        if (request) request.abort();
        request = null;
        timeout.stop();
        lines = [];
        status = "Looking for lyrics…";
        lookup.restart();
    }

    function fetchLyrics() {
        const title = player?.trackTitle || "";
        const artist = player?.trackArtist || "";
        if (!title || !artist) {
            status = "Synchronized lyrics unavailable";
            return;
        }
        const sequence = generation;
        const xhr = new XMLHttpRequest();
        request = xhr;
        const params = "track_name=" + encodeURIComponent(title) + "&artist_name=" + encodeURIComponent(artist);
        xhr.open("GET", "https://lrclib.net/api/search?" + params);
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE || sequence !== root.generation) return;
            root.request = null;
            timeout.stop();
            try {
                if (xhr.status !== 200) throw new Error("lookup failed");
                const results = JSON.parse(xhr.responseText);
                const length = root.player?.length || 0;
                const normalize = s => (s || "").toLowerCase().replace(/[.,!?()\[\]{}'"-]+/g, " ").replace(/\s+/g, " ").trim();
                const wantedTitle = normalize(title);
                const wantedArtist = normalize(artist);
                const matches = results.filter(r => r.syncedLyrics && normalize(r.trackName) === wantedTitle &&
                    normalize(r.artistName) && (normalize(r.artistName) === wantedArtist || normalize(r.artistName).includes(wantedArtist) || wantedArtist.includes(normalize(r.artistName))) &&
                    (!length || !r.duration || Math.abs(r.duration - length) <= 5));
                matches.sort((a, b) => Math.abs((a.duration || length) - length) - Math.abs((b.duration || length) - length));
                const parsed = matches.length ? Lyrics.parseLrc(matches[0].syncedLyrics) : [];
                root.lines = parsed;
                root.status = parsed.length ? "" : "Synchronized lyrics unavailable";
            } catch (e) {
                root.status = "Synchronized lyrics unavailable";
            }
        };
        timeout.restart();
        xhr.send();
    }

    Timer { id: lookup; interval: 400; onTriggered: root.fetchLyrics() }
    // MPRIS position advances between signals; the upstream card normally
    // refreshes it only every three seconds, which makes lyric changes late.
    Timer {
        interval: 150
        repeat: true
        running: root.player?.isPlaying ?? false
        onTriggered: root.player.positionChanged()
    }
    Timer {
        id: timeout
        interval: 10000
        onTriggered: {
            root.generation++;
            if (root.request) root.request.abort();
            root.request = null;
            root.status = "Synchronized lyrics unavailable";
        }
    }

    ColumnLayout {
        id: lyricColumn
        anchors.fill: parent
        spacing: 6
        Repeater {
            model: 3
            delegate: Text {
                required property int index
                readonly property int lyricIndex: root.currentLine + index - 1
                Layout.fillWidth: true
                Layout.minimumHeight: font.pixelSize * 1.35
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignLeft
                textFormat: Text.PlainText
                text: root.lines.length ? (root.lines[lyricIndex]?.text || "") : (index === 1 ? root.status : "")
                wrapMode: Text.Wrap
                font.family: Appearance.font.family.main
                font.pixelSize: index === 1 && root.lines.length ? 19 : 15
                font.weight: index === 1 && root.lines.length ? Font.Bold : Font.Medium
                color: index === 1 && root.lines.length ? root.textColor : root.mutedColor
                Behavior on color { ColorAnimation { duration: 180 } }
            }
        }
    }
}
