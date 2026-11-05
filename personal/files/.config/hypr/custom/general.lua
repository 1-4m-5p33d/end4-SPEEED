hl.config({
    input = {
        touchpad = {
            scroll_factor = 0.2
        }
    },
    decoration = {
        shadow = {
            -- Upstream used to set 10 here, which Hyprland rejects (max is 4).
            -- Keeping this override in custom/ means upstream can change its
            -- default without carrying a modified upstream file.
            render_power = 4
        }
    }
})