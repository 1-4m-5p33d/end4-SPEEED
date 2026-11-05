-- Bind to open this file in an editor
hl.bind("CTRL+SUPER+ALT+Slash", hl.dsp.exec_cmd("xdg-open ~/.config/hypr/custom/keybinds.lua"), { description = "Edit user keybinds" })

-- ============================================================================
-- FIX: "Super alone opens the overview" must not fire when Super is used as a
-- modifier (Super+W, Super+V, Super+., Super+drag, ...).
--
-- The ii shell decides this via `quickshell:searchToggleReleaseInterrupt`.
-- The original Hyprland config fired it from a catch-all bind in an
-- always-active `global` submap:
--     binditn = Super, catchall, global, quickshell:searchToggleReleaseInterrupt
-- The Lua port (upstream commit 010f070e) dropped that mechanism, so the
-- interrupt was never sent. As a result the overview toggled on *every* Super
-- release (so Super+W also showed the overview) and the clipboard/emoji popup
-- from Super+V / Super+. closed again the moment Super was released.
--
-- We reimplement the catch-all by watching raw key events: whenever a key
-- other than Super is pressed while Super is held, tell the shell to cancel the
-- pending release-toggle.
-- ============================================================================

local SUPER_KEYCODES = { [133] = true, [134] = true } -- XKB keycodes: Super_L, Super_R
local superDown = false

hl.on("input.keyboard.key", function(keycode, _timestamp, state)
    -- state: 0 = released, 1 = pressed, 2 = repeated
    if SUPER_KEYCODES[keycode] then
        superDown = (state ~= 0)
        return
    end
    if state ~= 1 or not superDown then
        return
    end
    hl.dispatch(hl.dsp.global("quickshell:searchToggleReleaseInterrupt"))
end)

-- Same for mouse buttons/scroll while Super is held (e.g. Super+drag to move a
-- window), otherwise releasing Super after a drag still toggles the overview.
for _, button in ipairs({ 272, 273, 274, 275, 276, 277 }) do
    hl.bind("SUPER + mouse:" .. button, hl.dsp.global("quickshell:searchToggleReleaseInterrupt"))
end
hl.bind("SUPER + mouse_up", hl.dsp.global("quickshell:searchToggleReleaseInterrupt"))
hl.bind("SUPER + mouse_down", hl.dsp.global("quickshell:searchToggleReleaseInterrupt"))
