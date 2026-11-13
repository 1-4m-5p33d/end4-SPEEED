.pragma library

function parseLrc(source) {
    const lines = [];
    const rows = source.split(/\r?\n/);
    for (let i = 0; i < rows.length; i++) {
        const stamps = [];
        const pattern = /\[(\d+):(\d{2})(?:[.:](\d{1,3}))?\]/g;
        let match;
        while ((match = pattern.exec(rows[i])) !== null) stamps.push(match);
        const text = rows[i].replace(/\[(\d+):(\d{2})(?:[.:](\d{1,3}))?\]/g, "").trim();
        for (const stamp of stamps) {
            const fraction = stamp[3] ? Number("0." + stamp[3]) : 0;
            lines.push({ time: Number(stamp[1]) * 60 + Number(stamp[2]) + fraction, text: text });
        }
    }
    return lines.sort((a, b) => a.time - b.time);
}

function currentIndex(lines, position) {
    let index = -1;
    for (let i = 0; i < lines.length && lines[i].time <= position; i++)
        index = i;
    return index;
}
