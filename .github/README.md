<div align="center">
    <h1>【 1-4m-5p33d's Hyprland setup 】</h1>
    <p>My personal Hyprland + Quickshell desktop, based on
    <a href="https://github.com/end-4/dots-hyprland">end-4/dots-hyprland</a>.</p>
</div>

<div align="center">
    <img src="personal/wallpapers/2024-Formula1-McLaren-MCL38-003-2800p.jpg" alt="Current wallpaper" width="720">
</div>

## About this repo

This is **my** day-to-day Arch Linux setup. It is a fork of
[end-4/dots-hyprland](https://github.com/end-4/dots-hyprland), but every change
I make lives in [`personal/`](personal/) instead of the upstream files, so I can
pull upstream updates without merge pain.

It is not meant to be a general-purpose distribution — it is the exact config I
use on my machine, kept here so a fresh install is two commands instead of a
weekend of tweaking.

## What I customized

- **Wallpaper + Material You theme** — the wallpaper above, with colors
  generated from it by matugen.
- **Clock** — digital, vertical, freely placed (position lives in
  `~/.config/illogical-impulse/config.json`).
- **Hyprland user layer** — touchpad scroll factor, the shadow
  `render_power` fix, and a fix so using Super as a modifier
  (`Super+W`, `Super+V`, `Super+.`, …) no longer opens the overview.
- **Lock screen** — 12-hour clock.
- **Bar / shell settings** — panel family, bar layout, weather, sidebar,
  overview, and the rest of the Quickshell config.

Fonts are intentionally the upstream defaults: **Google Sans Flex**,
**JetBrains Mono NF**, **Readex Pro**, and **Space Grotesk**. My local
`fontconfig` is not carried over.

## Install (new machine)

```bash
git clone git@github.com:1-4m-5p33d/end4-SPEEED.git
cd end4-SPEEED
./setup install
./personal/apply.sh
```

`./setup install` installs the base dotfiles and dependencies.
`./personal/apply.sh` then applies my overlay (Hyprland custom files, shell
config, wallpaper, lock screen) and regenerates the color scheme from the
wallpaper.

Monitor layout is machine-specific and is **not** tracked. Set it on the new
machine with `nwg-displays` or `hyprctl`.

## Update from upstream

```bash
git fetch upstream
git merge upstream/main        # or: git rebase upstream/main
./setup install
./personal/apply.sh
```

The `upstream` remote points at `https://github.com/end-4/dots-hyprland.git`.

## Save changes I make later

```bash
./personal/capture.sh
git diff -- personal
git add personal && git commit -m "personal: update config"
```

## How `personal/` is organized

```
personal/
├── apply.sh                 install the overlay on the current machine
├── capture.sh               copy the live config back into this repo
├── files/                   mirrors paths under $HOME
│   └── .config/
│       ├── illogical-impulse/config.json
│       └── hypr/
│           ├── custom/*.lua
│           ├── hyprlock.conf
│           └── hyprlock/colors.conf
└── wallpapers/              current wallpaper
```

See [`personal/README.md`](personal/README.md) for the details, including what
is deliberately not tracked and why.

## Credits

Base dotfiles: [end-4/dots-hyprland](https://github.com/end-4/dots-hyprland) by
end-4 and its contributors. This fork keeps the same license; see
[LICENSE](LICENSE).