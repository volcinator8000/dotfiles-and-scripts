# dotfiles-and-scripts

Arch Linux + Hyprland (Lua config) rice in a **cybersigilism** palette, plus the
scripts and small tools that go with it. One command puts everything in place.

```
bash <(curl -fsSL https://raw.githubusercontent.com/volcinator8000/dotfiles-and-scripts/main/install.sh)
```

The script clones this repo to `~/dotfiles-and-scripts`, installs packages,
symlinks the configs into `$HOME` (anything already there is moved to
`~/.config-backup-<date>/`), generates the key-sound packs, drops the root-side
files into `/etc`, enables timers and puts the user in the `input` group.
Running it again is a no-op for anything already done.

Flags: `--skip-packages` `--skip-system` `--apps` (Discord/Slack/Spotify/Zen)
`--hibernate` (btrfs swapfile + resume, interactive) `--dry-run`.

## What is in here

| path | what |
|---|---|
| `home/.config/hypr` | Hyprland `hyprland.lua`, hyprlock, hypridle, hyprpaper, hyprsunset |
| `home/.config/waybar` | bar + scripts: update checker, updater window, GPU/power-aware widget, lyrics, keep-awake eye |
| `home/.config/swaync` | notification center / control center with toggles (`keepawake.sh`, `nightlight.sh`) |
| `home/.config/keysound` | **sound theme**: evdev typewriter daemon + system sounds, pure-python synthesis, packs (cybersigil, animalese, frog). Each pack = 23 WAVs: `key0-3 space backspace mod enter hold release` (keys) + `notify notify-urgent lock unlock shutter plug unplug batt-low` (system). `keysound.sh play <event>` is what swaync, the lock wrapper, the screenshot script and the battery widget call |
| `home/.config/sigil-settings` | GTK4/libadwaita settings app (SUPER+I toggles; resident, autostarted hidden): dashboard, sounds, power, night light, idle timers, wallpaper gallery, services, input (keyboard/touchpad via `hypr/local.lua`) |
| `home/.config/hypr/scripts` | `lock.sh` (lock wrapper: away timer + lock/unlock sounds), `lock-info.sh` (battery/wifi/away labels), now-playing art + text for hyprlock, `shot.sh` (screenshots with shutter + notification) |
| `home/.config/spicetify/Themes/Cybersigil` | Spotify theme; apply with `sudo chmod a+wr -R /opt/spotify && spicetify backup apply` (redo after Spotify updates) |
| `home/.config/systemd/user` | `dots-sync.timer`: weekly auto commit + push of this repo (`dots-sync` by hand) |
| `home/.config/{kitty,rofi,wlogout,macchina,qt6ct,fontconfig}` | themed apps, fonts fallback chain (CJK/emoji) |
| `home/.zshrc`, `starship.toml` | zsh + oh-my-zsh + starship two-line prompt + macchina fetch |
| `scripts/bin/` | `dirprep` (Epitech C project scaffold), `mirmon` (mirror HDMI), `pt` (add/commit/push) → linked into `~/.local/bin` |
| `scripts/setup/` | one-off setup scripts: hibernation, dGPU wakeup fix, zsh rice, wallpaper generator |
| `system/etc/` | lid/hibernate logind+sleep drop-ins, power-key handling, power sysctl, wifi powersave, dGPU no-wakeup udev rule, spicetify pacman hook |
| `system/boot/refind-stanza.conf` | manual rEFInd stanza (append to `/boot/EFI/refind/refind.conf`) that refind-btrfs clones per snapshot; `system/etc/refind-btrfs.conf` pins the ESP |
| `system/reference/` | copies of mkinitcpio.conf / pacman.conf / snapper config, for reading only |
| `packages/` | `pacman.txt` (official), `aur.txt`, `apps.txt` |

## Palette

| name | hex |
|---|---|
| cherenkov glow blue (primary) | `#3ae0ff` |
| plasmatic purple | `#a64dff` |
| snooze button pink | `#ff5cc8` |
| communication red | `#ff2d3a` |
| graphical wavelength green | `#39ff14` |
| infrared sunset | `#ff5a1f` |
| phosphorus display amber | `#ffb000` |
| base / surface / line | `#050507` `#0d0d12` `#1b1b24` |

## Day to day

Configs in `~/.config` are symlinks into this repo, so edit them in place and:

```
dots status
dots add -A && dots commit -m "..."
dots push
```

## Ultra power saver (focus mode)

`ultra on|off|toggle|status` (`scripts/bin/ultra`, also SUPER+SHIFT+U, the Power page of the
settings app, `remote ultra` from the phone). Strips the session down to what is needed to
work and hands the battery back: animations, blur, shadows, rounding and the inactive fade
off, hardware cursor, panel at its lowest refresh mode (40 Hz), wallpaper daemon gone, a
minimal bar (`waybar/config-ultra.jsonc`), dim 30 s / lock 2 min / screen off 3 min /
suspend 5 min, key sounds and night light stopped, power-saver profile, backlight capped,
bluetooth off, and the chat/music apps closed (relaunched on exit). Knobs are the `ultra_*`
keys in `hypr/power-auto.conf`; `battery.sh` leaves the mode when the charger is plugged and
can enter it below a percentage. `ultra off` restores everything through `hyprctl reload`;
nothing persists across a reboot.

The root half is optional: `system/usr/local/bin/sigil-powerctl` (CPU boost off, clock cap,
amdgpu panel ABM) with the NOPASSWD rule in `system/etc/sudoers.d/`, both installed by
`install.sh` (sudoers files go in with mode 0440 after a `visudo -c`). Without it `ultra`
just says so and does the rest.

## Machine-specific bits

Written on an HP laptop with a Ryzen 7535HS (680M iGPU) + RX 6500M dGPU, AZERTY
keyboard, 1920x1080 panel. Things that assume that hardware:

- `waybar/scripts/gpu.sh` reads `card1` runtime-PM status (never poll amdgpu sysfs stats on a short interval, it wakes the card)
- backlight device `amdgpu_bl2` in swaync's backlight widget
- `system/etc/udev/rules.d/90-dgpu-no-wakeup.rules` names PCI addresses; the installer only applies it if an AMD GPU sits at `01:00.0`
- `system/etc/udev/rules.d/80-power-runtime.rules.off` and `dgpu-perf-pin.service` are suspects in the 2026-09-15..22 freeze / "data fabric sync flood" incident (see the memory notes); the rule stays disabled and the service should stay off until the machine has been stable for a while, then re-enable one at a time
- hibernation needs a resume offset and a kernel command line edit; `--hibernate` runs the interactive script
- `hyprland.lua` uses the Hyprland ≥ 0.56 Lua API, and `hyprctl dispatch` takes Lua syntax on that build
