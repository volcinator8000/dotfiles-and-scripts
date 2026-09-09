-- This is an example Hyprland Lua config file.
-- Refer to the wiki for more information.
-- https://wiki.hypr.land/Configuring/Start/

-- Please note not all available settings / options are set here.
-- For a full list, see the wiki

-- You can (and should!!) split this configuration into multiple files
-- Create your files separately and then require them like this:
-- require("myColors")

------------------
---- MONITORS ----
------------------

-- See https://wiki.hypr.land/Configuring/Basics/Monitors/
hl.monitor({
    output = "",
    mode = "highres",
    position = "auto",
    scale = 1,
})

---------------------
---- MY PROGRAMS ----
---------------------

-- Set programs that you use
local terminal = "kitty"
local fileManager = "dolphin"
local menu = "rofi -show drun"
local browser = "zen-browser"
local ide = "code"

-------------------
---- AUTOSTART ----
-------------------

-- See https://wiki.hypr.land/Configuring/Basics/Autostart/

-- Autostart necessary processes (like notifications daemons, status bars, etc.)
-- Or execute your favorite apps at launch like this:
--
hl.on("hyprland.start", function ()
    -- Restart portals after Hyprland is up so xdg-desktop-portal binds the
    -- Hyprland backend (fixes Discord/screenshare when portals win the boot race)
    hl.exec_cmd("bash -c 'sleep 1; systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal'")
    hl.exec_cmd("systemctl --user start hyprpolkitagent") -- GUI auth prompts (pkexec etc.)
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("waybar")
    hl.exec_cmd("[workspace special:vesktop silent] vesktop")
    hl.exec_cmd("[workspace special:slack silent] slack")
    hl.exec_cmd("[workspace special:spotify silent] spotify")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("kdeconnect-indicator") -- phone link (KDE Connect): notifications, clipboard, files, media; tray icon
    hl.exec_cmd("playerctld daemon") -- follows the most recently active media player (bar title + lyrics)
    hl.exec_cmd("hypridle")
    hl.exec_cmd("swaync")
    hl.exec_cmd("hyprexpose")
    hl.exec_cmd("~/.config/keysound/keysound.sh start") -- typewriter key sounds
    hl.exec_cmd("wl-paste --type text --watch cliphist store")  -- clipboard history (SUPER+SHIFT+V)
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
    hl.exec_cmd("~/.config/swaync/nightlight.sh autostart") -- night light schedule if enabled (~/.config/hypr/hyprsunset.conf)
    hl.exec_cmd("bash -c 'sleep 8; python3 ~/.config/sigil-settings/sigil-settings.py --hidden'") -- settings app resident in the background
end)

-------------------------------
---- ENVIRONMENT VARIABLES ----
-------------------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Environment-variables/

hl.env("XCURSOR_THEME", "catppuccin-mocha-dark-cursors")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_THEME", "catppuccin-mocha-dark-cursors")
hl.env("HYPRCURSOR_SIZE", "24")
hl.env("GDK_DISABLE", "vulkan") -- GTK4 Vulkan probe wakes the suspended dGPU (~2 s) on every app launch; GL renderer instead
hl.env("GTK_A11Y", "none") -- no accessibility bus/registry daemons for GTK4 apps
hl.env("NO_AT_BRIDGE", "1") -- same for GTK3

-- Qt theming: qt6ct/qt5ct with the Kvantum style set inside their configs
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")

-----------------------
----- PERMISSIONS -----
-----------------------

-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Permissions/
-- Please note permission changes here require a Hyprland restart and are not applied on-the-fly
-- for security reasons

-- hl.config({
--     ecosystem = {
--         enforce_permissions = true,
--     },
-- })

-- hl.permission("/usr/(bin|local/bin)/grim", "screencopy", "allow")
-- hl.permission("/usr/(lib|libexec|lib64)/xdg-desktop-portal-hyprland", "screencopy", "allow")
-- hl.permission("/usr/(bin|local/bin)/hyprpm", "plugin", "allow")

-----------------------
---- LOOK AND FEEL ----
-----------------------

-- Refer to https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
    general = {
        gaps_in = 4,
        gaps_out = 8,

        border_size = 1,

        -- cybersigilism: cherenkov blue -> plasmatic purple -> snooze pink
        col = {
            active_border = { colors = {"rgba(3ae0ffff)", "rgba(a64dffff)", "rgba(ff5cc8ff)"}, angle = 30 },
            inactive_border = "rgba(1b1b24ff)",
        },

        -- Set to true to enable resizing windows by clicking and dragging on borders and gaps
        resize_on_border = false,

        -- Please see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Tearing/ before you turn this on
        allow_tearing = false,

        layout = "dwindle",
    },

    decoration = {
        rounding = 2,
        rounding_power = 2,

        -- Change transparency of focused and unfocused windows
        active_opacity = 1.0,
        inactive_opacity = 0.95,

        shadow = {
            enabled = true,
            range = 18,
            render_power = 4,
            color = "rgba(3ae0ff2a)",
            color_inactive = "rgba(00000099)",
        },

        blur = {
            enabled = true,
            size = 6,
            passes = 2,
            vibrancy = 0.17,
            popups = true,
        },
    },

    animations = {
        enabled = true,
    },
})

-- Default curves and animations, see https://wiki.hypr.land/Configuring/Advanced-and-Cool/Animations/
hl.curve("easeOutQuint", { type = "bezier", points = { {0.23, 1}, {0.32, 1} } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1} } })
hl.curve("linear", { type = "bezier", points = { {0, 0}, {1, 1} } })
hl.curve("almostLinear", { type = "bezier", points = { {0.5, 0.5}, {0.75, 1} } })
hl.curve("quick", { type = "bezier", points = { {0.15, 0}, {0.1, 1} } })

-- Default springs
hl.curve("easy", { type = "spring", mass = 1, stiffness = 71.2633, dampening = 15.8273644 })

hl.animation({ leaf = "global", enabled = true, speed = 10, bezier = "default" })
hl.animation({ leaf = "border", enabled = true, speed = 5.39, bezier = "easeOutQuint" })
hl.animation({ leaf = "windows", enabled = true, speed = 4.79, spring = "easy" })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 4.1, spring = "easy", style = "popin 87%" })
hl.animation({ leaf = "windowsOut", enabled = true, speed = 1.49, bezier = "linear", style = "popin 87%" })
hl.animation({ leaf = "fadeIn", enabled = true, speed = 1.73, bezier = "almostLinear" })
hl.animation({ leaf = "fadeOut", enabled = true, speed = 1.46, bezier = "almostLinear" })
hl.animation({ leaf = "fade", enabled = true, speed = 3.03, bezier = "quick" })
hl.animation({ leaf = "layers", enabled = true, speed = 3.81, bezier = "easeOutQuint" })
hl.animation({ leaf = "layersIn", enabled = true, speed = 4, bezier = "easeOutQuint", style = "fade" })
hl.animation({ leaf = "layersOut", enabled = true, speed = 1.5, bezier = "linear", style = "fade" })
hl.animation({ leaf = "fadeLayersIn", enabled = true, speed = 1.79, bezier = "almostLinear" })
hl.animation({ leaf = "fadeLayersOut", enabled = true, speed = 1.39, bezier = "almostLinear" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesIn", enabled = true, speed = 1.21, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "workspacesOut", enabled = true, speed = 1.94, bezier = "almostLinear", style = "fade" })
hl.animation({ leaf = "zoomFactor", enabled = true, speed = 7, bezier = "quick" })

-- Ref https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/
-- "Smart gaps" / "No gaps when only"
-- uncomment all if you wish to use that.
-- hl.workspace_rule({ workspace = "w[tv1]", gaps_out = 0, gaps_in = 0 })
-- hl.workspace_rule({ workspace = "f[1]", gaps_out = 0, gaps_in = 0 })
-- hl.window_rule({
--     name = "no-gaps-wtv1",
--     match = { float = false, workspace = "w[tv1]" },
--     border_size = 0,
--     rounding = 0,
-- })
-- hl.window_rule({
--     name = "no-gaps-f1",
--     match = { float = false, workspace = "f[1]" },
--     border_size = 0,
--     rounding = 0,
-- })

hl.window_rule({
    name = "spotify-to-special",
    match = { class = "Spotify" },
    workspace = "special:spotify"
})

hl.window_rule({
    name = "vesktop-to-special",
    match = { class = "vesktop" },
    workspace = "special:vesktop"
})

hl.window_rule({
    name = "slack-to-special",
    match = { class = "[Ss]lack" },
    workspace = "special:slack"
})

-- See https://wiki.hypr.land/Configuring/Layouts/Dwindle-Layout/ for more
hl.config({
    dwindle = {
        preserve_split = true, -- You probably want this
    },
})

-- See https://wiki.hypr.land/Configuring/Layouts/Master-Layout/ for more
hl.config({
    master = {
        new_status = "master",
    },
})

-- See https://wiki.hypr.land/Configuring/Layouts/Scrolling-Layout/ for more
hl.config({
    scrolling = {
        fullscreen_on_one_column = true,
    },
})

----------------
---- MISC ----
----------------

hl.config({
    cursor = {
        -- Software cursor so it gets composited into screenshares/recordings
        no_hardware_cursors = true,
    },
})

hl.config({
    misc = {
        force_default_wallpaper = -1,
        disable_hyprland_logo = true,
        mouse_move_enables_dpms = true,
        -- false: a keypress while the panel is dark is delivered to the app (e.g. hyprlock)
        -- instead of being swallowed to wake the screen; hypridle turns the panel on anyway
        key_press_enables_dpms = false,
    },
})

---------------
---- INPUT ----
---------------

hl.config({
    input = {
        kb_layout = "fr",
        kb_variant = "azerty",
        resolve_binds_by_sym = 1,
        kb_model = "",
        kb_options = "",
        kb_rules = "",

        follow_mouse = 1,

        sensitivity = -0.15, -- -1.0 - 1.0, 0 means no modification.

        touchpad = {
            natural_scroll = true,
        },
    },
})

hl.gesture({
    fingers = 3,
    direction = "horizontal",
    action = "workspace"
})

-- 1. Swipe 3 fingers UP -> toggle the hidden "vesktop" workspace
hl.gesture({
    fingers = 3,
    direction = "up",
    action = "special",
    workspace_name = "vesktop"
})

-- 2. Pinch -> open Spotify
hl.gesture({ 
    fingers = 4, 
    direction = "up", 
    action = "special",
    workspace_name = "spotify"
})

-- 3. Swipe 3 fingers DOWN -> toggle the special "magic" workspace
hl.gesture({
    fingers = 3,
    direction = "down",
    action = "special",
    workspace_name = "magic"
})

-- 4. Swipe 4 fingers DOWN -> toggle the hidden "slack" workspace
hl.gesture({
    fingers = 4,
    direction = "down",
    action = "special",
    workspace_name = "slack"
})

-- Example per-device config
-- See https://wiki.hypr.land/Configuring/Advanced-and-Cool/Devices/ for more
hl.device({
    name = "epic-mouse-v1",
    sensitivity = -0.5,
})

---------------------
---- KEYBINDINGS ----
---------------------


-- screenshot stuff

-- Region screenshot, opens in satty for annotation, Ctrl+C copies, Ctrl+S saves
hl.bind("Print", hl.dsp.exec_cmd("~/.config/hypr/scripts/shot.sh region"))          -- region -> satty (annotate, copy, save)

-- Full screen, direct to clipboard
hl.bind("SUPER + Print", hl.dsp.exec_cmd("~/.config/hypr/scripts/shot.sh copy"))    -- region -> clipboard
hl.bind("SUPER + SHIFT + Print", hl.dsp.exec_cmd("~/.config/hypr/scripts/shot.sh window")) -- active window -> file + clipboard
hl.bind("SUPER + ALT + Print", hl.dsp.exec_cmd("~/.config/hypr/scripts/shot.sh full"))    -- whole screen -> file + clipboard

-- Fallback bind if laptop sends XF86SELECTIVESCREENSHOT instead of Print
hl.bind("XF86SELECTIVESCREENSHOT", hl.dsp.exec_cmd("~/.config/hypr/scripts/shot.sh region"))


-- overview mode
hl.bind("SUPER + Tab", hl.dsp.exec_cmd("pkill -SIGUSR1 hyprexpose"))


-- Lid close: only lock. systemd-logind already suspends on lid close (HandleLidSwitch),
-- and hypridle (inhibit_sleep = 3) holds the suspend until hyprlock is drawn.
-- Do NOT call systemctl suspend here: the command survives the sleep and fires
-- again on resume, which caused the double-suspend on lid open.
hl.bind("switch:on:Lid Switch", hl.dsp.exec_cmd("loginctl lock-session"), { locked = true })


local mainMod = "SUPER" -- Sets "Windows" key as main modifier

hl.bind(mainMod .. " + L", hl.dsp.exec_cmd("loginctl lock-session"))
hl.bind("XF86PowerOff", hl.dsp.exec_cmd("~/.config/keysound/keysound.sh play open; wlogout"), { locked = true }) -- power button: menu, not poweroff (logind HandlePowerKey=ignore)
hl.bind(mainMod .. " + N", hl.dsp.exec_cmd("~/.config/keysound/keysound.sh play open; swaync-client -t -sw"))
hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("~/.config/rofi/clip.sh")) -- clipboard history
hl.bind(mainMod .. " + O", hl.dsp.exec_cmd("~/.config/keysound/keysound.sh play open; rofi -show emoji")) -- emoji picker (rofi-emoji)
hl.bind(mainMod .. " + I", hl.dsp.exec_cmd("python3 ~/.config/sigil-settings/sigil-settings.py --toggle")) -- settings applet (resident, toggles)

-- Example binds, see https://wiki.hypr.land/Configuring/Basics/Binds/ for more
hl.bind(mainMod .. " + T", hl.dsp.exec_cmd(terminal))
local closeWindowBind = hl.bind(mainMod .. " + Q", hl.dsp.window.close())
-- closeWindowBind:set_enabled(false)
hl.bind(mainMod .. " + E", hl.dsp.exec_cmd(fileManager))
hl.bind(mainMod .. " + B", hl.dsp.exec_cmd(browser))
hl.bind(mainMod .. " + C", hl.dsp.exec_cmd(ide))
hl.bind(mainMod .. " + V", hl.dsp.window.float({ action = "toggle" }))
hl.bind(mainMod .. " + F", hl.dsp.window.fullscreen())
hl.bind(mainMod .. " + R", hl.dsp.exec_cmd("~/.config/keysound/keysound.sh play open; " .. menu))
hl.bind(mainMod .. " + SHIFT + P", hl.dsp.window.pseudo()) -- pseudo-tile (moved off plain SUPER+P)
hl.bind(mainMod .. " + J", hl.dsp.layout("togglesplit")) -- dwindle only

-- Move focus with mainMod + arrow keys
hl.bind(mainMod .. " + left", hl.dsp.focus({ direction = "left" }))
hl.bind(mainMod .. " + right", hl.dsp.focus({ direction = "right" }))
hl.bind(mainMod .. " + up", hl.dsp.focus({ direction = "up" }))
hl.bind(mainMod .. " + down", hl.dsp.focus({ direction = "down" }))

-- Switch workspaces with mainMod + AZERTY top row keys
-- Move active window to a workspace with mainMod + SHIFT + AZERTY top row keys
local azerty_keys = {
    "ampersand",  -- 1: &
    "eacute",     -- 2: é
    "quotedbl",   -- 3: "
    "apostrophe", -- 4: '
    "parenleft",  -- 5: (
    "minus",      -- 6: -
    "egrave",     -- 7: è
    "underscore", -- 8: _
    "ccedilla",   -- 9: ç
    "agrave"      -- 0: à
}

for i = 1, 10 do
    local key = azerty_keys[i]
    hl.bind(mainMod .. " + " .. key, hl.dsp.focus({ workspace = i}))
    hl.bind(mainMod .. " + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }))
end



-- picture-in-picture: float, pin, and shrink the active window
hl.bind(mainMod .. " + P", function()
    hl.dispatch(hl.dsp.window.float({ action = "set" }))
    hl.dispatch(hl.dsp.window.pin())
    hl.dispatch(hl.dsp.window.resize({ x = 800, y = 450, relative = false }))
end)


-- Example special workspace (scratchpad)
hl.bind(mainMod .. " + S", hl.dsp.workspace.toggle_special("magic"))
hl.bind(mainMod .. " + SHIFT + S", hl.dsp.window.move({ workspace = "special:magic" }))

--special workspace vesktop

hl.bind(mainMod .. " + D", hl.dsp.workspace.toggle_special("vesktop"))
hl.bind(mainMod .. " + SHIFT + D", hl.dsp.window.move({ workspace = "special:vesktop" }))

--special workspace spotify

hl.bind(mainMod .. " + M", hl.dsp.workspace.toggle_special("spotify"))
hl.bind(mainMod .. " + SHIFT + M", hl.dsp.window.move({ workspace = "special:spotify" }))


-- Scroll through existing workspaces with mainMod + scroll
hl.bind(mainMod .. " + mouse_down", hl.dsp.focus({ workspace = "e+1" }))
hl.bind(mainMod .. " + mouse_up", hl.dsp.focus({ workspace = "e-1" }))

-- Move/resize windows with mainMod + LMB/RMB and dragging
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })

-- Laptop multimedia keys for volume and LCD brightness
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { locked = true, repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { locked = true, repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), { locked = true, repeating = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%+"), { locked = true, repeating = true })
hl.bind("XF86MonBrightnessDown",hl.dsp.exec_cmd("brightnessctl -e4 -n2 set 5%-"), { locked = true, repeating = true })

-- Requires playerctl
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"), { locked = true })
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"), { locked = true })

--------------------------------
---- WINDOWS AND WORKSPACES ----
--------------------------------

-- See https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- and https://wiki.hypr.land/Configuring/Basics/Workspace-Rules/

-- Example window rules that are useful

local suppressMaximizeRule = hl.window_rule({
    -- Ignore maximize requests from all apps. You'll probably like this.
    name = "suppress-maximize-events",
    match = { class = ".*" },

    suppress_event = "maximize",
})
-- suppressMaximizeRule:set_enabled(false)

hl.window_rule({
    -- Fix some dragging issues with XWayland
    name = "fix-xwayland-drags",
    match = {
        class = "^$",
        title = "^$",
        xwayland = true,
        float = true,
        fullscreen = false,
        pin = false,
    },

    no_focus = true,
})

-- Layer rules also return a handle.
-- local overlayLayerRule = hl.layer_rule({
--     name = "no-anim-overlay",
--     match = { namespace = "^my-overlay$" },
--     no_anim = true,
-- })
-- overlayLayerRule:set_enabled(false)

-- Update window opened from the waybar updates module
hl.window_rule({
    name = "float-system-update",
    match = { title = "^system-update$" },
    float = true,
    center = true,
    size = "1500 860",
})

hl.window_rule({
    name = "float-sigil-settings",
    match = { class = "^io\\.sigil\\.Settings$" },
    float = true,
    center = true,
    size = "980 680",
})

-- Float common utility popups
hl.window_rule({
    name = "float-utilities",
    match = { class = "^(pavucontrol|nm-connection-editor|blueman-manager|org.pulseaudio.pavucontrol)$" },
    float = true,
    size = "60% 60%",
    center = true,
})

-- Layer rules: blur waybar / launcher / notifications
hl.layer_rule({ name = "blur-waybar", match = { namespace = "^waybar$" }, blur = true, ignore_alpha = 0.3 })
hl.layer_rule({ name = "blur-rofi",   match = { namespace = "^rofi$" },   blur = true, ignore_alpha = 0.3 })
hl.layer_rule({ name = "blur-swaync", match = { namespace = "^swaync-.*$" }, blur = true, ignore_alpha = 0.3 })

-- hyprsunset (night light) + the animated CTM fade make NEW WINDOWS NEVER MAP
-- (GTK4 clients spin at 100% CPU, verified 2026-09-07). Fade off = everything works.
hl.config({ render = { ctm_animation = 0 } })

-- machine-local overrides written by the settings app; errors there must never kill the session
pcall(dofile, os.getenv("HOME") .. "/.config/hypr/local.lua")
