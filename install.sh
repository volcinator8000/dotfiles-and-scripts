#!/usr/bin/env bash
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  dotfiles-and-scripts :: injection script                               │
# │  Arch Linux + Hyprland "cybersigilism" rice by volcinator8000            │
# │                                                                         │
# │  Fresh machine:                                                         │
# │    bash <(curl -fsSL https://raw.githubusercontent.com/volcinator8000/dotfiles-and-scripts/main/install.sh)
# │                                                                         │
# │  Already cloned:   ./install.sh [--skip-packages] [--skip-system]       │
# │                    [--apps] [--hibernate] [--dry-run]                   │
# └─────────────────────────────────────────────────────────────────────────┘
set -euo pipefail

REPO_URL="git@github.com:volcinator8000/dotfiles-and-scripts.git"
REPO_HTTPS="https://github.com/volcinator8000/dotfiles-and-scripts.git"
REPO_DIR="${DOTFILES_DIR:-$HOME/dotfiles-and-scripts}"

SKIP_PACKAGES=0 SKIP_SYSTEM=0 APPS=0 HIBERNATE=0 DRY=0
for a in "$@"; do
    case "$a" in
        --skip-packages) SKIP_PACKAGES=1 ;;
        --skip-system)   SKIP_SYSTEM=1 ;;
        --apps)          APPS=1 ;;
        --hibernate)     HIBERNATE=1 ;;
        --dry-run)       DRY=1 ;;
        -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
        *) echo "unknown flag: $a"; exit 1 ;;
    esac
done

# ── colours / helpers ────────────────────────────────────────────────────────
B=$'\e[38;2;58;224;255m' P=$'\e[38;2;166;77;255m' G=$'\e[38;2;57;255;20m' A=$'\e[38;2;255;176;0m' R=$'\e[38;2;255;45;58m' M=$'\e[38;2;107;107;120m' N=$'\e[0m'
say()  { printf '%s>>%s %s\n' "$B" "$N" "$*"; }
ok()   { printf '%s ok%s %s\n' "$G" "$N" "$*"; }
warn() { printf '%s !!%s %s\n' "$A" "$N" "$*"; }
die()  { printf '%s xx%s %s\n' "$R" "$N" "$*"; exit 1; }
run()  { if (( DRY )); then printf '%s   dry:%s %s\n' "$M" "$N" "$*"; else "$@"; fi; }

banner() {
    printf '%s' "$P"
    cat <<'EOF'
   ____  _  __ _  _
  / ___|| |/ _` || |      cybersigilism rice
  \___ \| | (_| || |      arch + hyprland
   ___) | |\__, || |___   injecting...
  |____/|_||___/ |_____|
EOF
    printf '%s\n' "$N"
}

# ── 0. make sure we run from a full clone, not from a curl pipe ─────────────
bootstrap() {
    command -v git >/dev/null || { say "installing git"; sudo pacman -S --needed --noconfirm git; }
    if [[ ! -d "$REPO_DIR/.git" ]]; then
        say "cloning into $REPO_DIR"
        git clone "$REPO_URL" "$REPO_DIR" 2>/dev/null || git clone "$REPO_HTTPS" "$REPO_DIR"
    else
        say "updating $REPO_DIR"
        git -C "$REPO_DIR" pull --ff-only || warn "pull failed, continuing with what is on disk"
    fi
    exec bash "$REPO_DIR/install.sh" "$@"
}
SELF="$(readlink -f "${BASH_SOURCE[0]:-}" 2>/dev/null || true)"
if [[ "$SELF" != "$(readlink -f "$REPO_DIR")/install.sh" ]]; then
    banner; bootstrap "$@"
fi
cd "$REPO_DIR"
banner
[[ -f /etc/arch-release ]] || warn "this is written for Arch Linux; package steps will probably fail elsewhere"

# ── 1. packages ──────────────────────────────────────────────────────────────
if (( ! SKIP_PACKAGES )); then
    say "official packages (pacman)"
    run sudo pacman -Syu --needed --noconfirm $(grep -vE '^\s*(#|$)' packages/pacman.txt)
    if ! command -v paru >/dev/null; then
        say "bootstrapping paru (AUR helper)"
        run sudo pacman -S --needed --noconfirm base-devel
        tmp="$(mktemp -d)"
        run git clone https://aur.archlinux.org/paru-bin.git "$tmp/paru-bin"
        (cd "$tmp/paru-bin" && run makepkg -si --noconfirm)
    fi
    say "AUR packages (paru)"
    run paru -S --needed --noconfirm $(grep -vE '^\s*(#|$)' packages/aur.txt)
    if (( APPS )); then
        say "apps (paru)"
        run paru -S --needed --noconfirm $(grep -vE '^\s*(#|$)' packages/apps.txt)
    fi
else
    warn "skipping packages"
fi

# ── 2. link home files ───────────────────────────────────────────────────────
# whole directories: everything in them is ours
LINK_DIRS=(
    .config/hypr .config/waybar .config/swaync .config/kitty .config/rofi .config/wlogout
    .config/keysound .config/sigil-settings .config/macchina .config/fontconfig .config/qt6ct
)
# single files: the directory around them holds other stuff we do not manage
LINK_FILES=(
    .zshrc .config/starship.toml .config/kdeglobals .config/dolphinrc
    .config/gtk-3.0/gtk.css .config/gtk-4.0/gtk.css
    .local/share/color-schemes/Cybersigil.colors
    .local/share/applications/sigil-settings.desktop
    .config/systemd/user/dots-sync.service .config/systemd/user/dots-sync.timer
    .config/systemd/user/swaync-watchdog.service .config/systemd/user/swaync-watchdog.timer
    .config/spicetify/Themes/Cybersigil
    Pictures/Wallpapers/cybersigil.png
)
BACKUP="$HOME/.config-backup-$(date +%Y%m%d-%H%M%S)"
link() {  # link <relative path>
    local rel="$1" src="$REPO_DIR/home/$1" dst="$HOME/$1"
    [[ -e "$src" ]] || { warn "missing in repo: $rel"; return; }
    if [[ -L "$dst" && "$(readlink -f "$dst")" == "$(readlink -f "$src")" ]]; then
        return  # already ours
    fi
    if [[ -e "$dst" || -L "$dst" ]]; then
        run mkdir -p "$BACKUP/$(dirname "$rel")"
        run mv "$dst" "$BACKUP/$rel"
        printf '%s   moved old %s -> %s%s\n' "$M" "$rel" "$BACKUP" "$N"
    fi
    run mkdir -p "$(dirname "$dst")"
    run ln -s "$src" "$dst"
    ok "$rel"
}
say "linking config into $HOME"
for d in "${LINK_DIRS[@]}"; do link "$d"; done
for f in "${LINK_FILES[@]}"; do link "$f"; done

say "linking scripts into ~/.local/bin"
run mkdir -p "$HOME/.local/bin"
for s in scripts/bin/*; do
    n="$(basename "$s")"
    run chmod +x "$s"
    if [[ ! -L "$HOME/.local/bin/$n" || "$(readlink -f "$HOME/.local/bin/$n")" != "$(readlink -f "$s")" ]]; then
        run ln -sf "$REPO_DIR/$s" "$HOME/.local/bin/$n"; ok "bin/$n"
    fi
done
run chmod +x scripts/setup/*.sh home/.config/waybar/scripts/* home/.config/swaync/*.sh home/.config/hypr/scripts/*.sh \
    home/.config/keysound/keysound.sh home/.config/sigil-settings/sigil-settings.py home/.config/rofi/*.sh 2>/dev/null || true

# ── 3. absolute paths that tools refuse to expand ────────────────────────────
# hyprpaper / hyprlock / qt6ct want real paths; rewrite whatever home they were saved with
say "fixing absolute home paths for $HOME"
fixpath() {  # fixpath <file> <sed expression>; only touches the file when something changes
    local before; before="$(cat "$1")"
    if [[ "$before" != "$(sed -e "$2" "$1")" ]]; then run sed -i -e "$2" "$1"; ok "$1"; fi
}
fixpath home/.config/hypr/hyprpaper.conf "s|= *[^ ]*/Pictures/Wallpapers/|= $HOME/Pictures/Wallpapers/|"
fixpath home/.config/hypr/hyprlock.conf  "s|= *[^ ]*/Pictures/Wallpapers/|= $HOME/Pictures/Wallpapers/|"
fixpath home/.config/qt6ct/qt6ct.conf    "s|color_scheme_path=.*/.config/qt6ct/|color_scheme_path=$HOME/.config/qt6ct/|"

# ── 4. generated bits ────────────────────────────────────────────────────────
say "generating key-sound packs"
for p in cybersigil animalese frog; do run python3 home/.config/keysound/gen-sounds.py --pack "$p" >/dev/null; done
grep -q '^pack=' home/.config/keysound/config || echo "pack=cybersigil" >> home/.config/keysound/config
say "font cache / desktop database / zsh plugins"
run fc-cache -f >/dev/null
command -v update-desktop-database >/dev/null && run update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
    say "installing oh-my-zsh (unattended, keeps our .zshrc)"
    run env ZSH="$HOME/.oh-my-zsh" RUNZSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi
ZC="$HOME/.oh-my-zsh/custom/plugins"
[[ -d "$ZC/zsh-autosuggestions" ]]     || run git clone -q https://github.com/zsh-users/zsh-autosuggestions "$ZC/zsh-autosuggestions" || true
[[ -d "$ZC/zsh-syntax-highlighting" ]] || run git clone -q https://github.com/zsh-users/zsh-syntax-highlighting "$ZC/zsh-syntax-highlighting" || true
[[ -d "$ZC/zsh-history-substring-search" ]] || run git clone -q https://github.com/zsh-users/zsh-history-substring-search "$ZC/zsh-history-substring-search" || true
run mkdir -p "$HOME/Pictures/Screenshots" "$HOME/.cache/nowplaying"
say "weekly dotfiles sync timer"
run systemctl --user daemon-reload 2>/dev/null || true
run systemctl --user enable --now dots-sync.timer swaync-watchdog.timer 2>/dev/null || warn "could not enable dots-sync.timer (no user session bus?)"
if [[ ! -x "$HOME/.spicetify/spicetify" ]] && command -v spotify >/dev/null; then
    say "spicetify (user install, themes Spotify); apply needs: sudo chmod a+wr -R /opt/spotify && spicetify backup apply"
    run sh -c "$(curl -fsSL https://raw.githubusercontent.com/spicetify/cli/main/install.sh)" </dev/null >/dev/null 2>&1 || warn "spicetify install failed"
    [[ -x "$HOME/.spicetify/spicetify" ]] && run "$HOME/.spicetify/spicetify" config current_theme Cybersigil color_scheme cybersigil inject_css 1 replace_colors 1 >/dev/null 2>&1 || true
fi

# ── 5. system side (needs sudo) ──────────────────────────────────────────────
if (( ! SKIP_SYSTEM )); then
    say "system files (sudo)"
    while IFS= read -r f; do
        rel="${f#system/etc/}"
        if [[ "$rel" == udev/rules.d/90-dgpu-no-wakeup.rules ]] && ! lspci -s 01:00.0 2>/dev/null | grep -qi 'navi\|radeon\|AMD'; then
            warn "skipping $rel: no AMD dGPU at 01:00.0 (that rule is for the RX 6500M laptop)"; continue
        fi
        if ! sudo cmp -s "$f" "/etc/$rel" 2>/dev/null; then
            run sudo install -Dm644 "$f" "/etc/$rel"; ok "/etc/$rel"
        fi
    done < <(find system/etc -type f | sort)
    say "services, groups, shell"
    run sudo systemctl enable --now paccache.timer fstrim.timer power-profiles-daemon bluetooth NetworkManager 2>/dev/null || true
    run sudo sysctl --system >/dev/null 2>&1 || true
    id -nG "$USER" | grep -qw input || { run sudo usermod -aG input "$USER"; warn "added to 'input' group (key sounds): relogin needed"; }
    [[ "$(getent passwd "$USER" | cut -d: -f7)" == "$(command -v zsh)" ]] || run chsh -s "$(command -v zsh)"
    command -v pkgfile >/dev/null && run sudo pkgfile -u >/dev/null 2>&1 || true
    if (( HIBERNATE )); then
        say "hibernation (btrfs swapfile + resume hook + refind); interactive"
        run bash scripts/setup/setup-hibernate.sh
    fi
else
    warn "skipping system files / services (--skip-system)"
fi

# ── 6. live reload if a session is running ──────────────────────────────────
if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" ]] && command -v hyprctl >/dev/null && (( ! DRY )); then
    say "reloading running session"
    hyprctl reload >/dev/null 2>&1 || true
    pkill -x waybar 2>/dev/null || true; sleep 0.3; hyprctl dispatch 'hl.dsp.exec_cmd("waybar")' >/dev/null 2>&1 || true
    swaync-client -R >/dev/null 2>&1 && swaync-client -rs >/dev/null 2>&1 || true
fi

printf '\n%s done.%s\n' "$G" "$N"
cat <<EOF
  repo      $REPO_DIR   (alias: dots status / dots add / dots commit / dots push)
  hyprland  log out and pick Hyprland; SUPER+I = settings, SUPER+R = launcher, SUPER+N = control center
  todo      hibernation is machine-specific: run with --hibernate on a btrfs swapfile setup
            the waybar backlight/gpu scripts assume an AMD laptop (amdgpu_bl*, card1)
EOF
