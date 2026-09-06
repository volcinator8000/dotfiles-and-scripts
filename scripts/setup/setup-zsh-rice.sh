#!/bin/bash
# Automated zsh rice setup for Arch Linux
# Installs: Nerd Font, Starship prompt, autosuggestions, syntax highlighting,
# eza/bat/zoxide/fzf, and wires everything into ~/.zshrc
set -e

echo "==> Installing packages..."
sudo pacman -S --needed --noconfirm \
    ttf-jetbrains-mono-nerd \
    zsh-autosuggestions \
    zsh-syntax-highlighting \
    eza bat zoxide fzf pkgfile

echo "==> Updating pkgfile database (for command-not-found)..."
sudo pkgfile --update
sudo systemctl enable --now pkgfile-update.timer

echo "==> Installing Starship..."
if ! command -v starship &>/dev/null; then
    curl -sS https://starship.rs/install.sh | sh -s -- -y
else
    echo "Starship already installed, skipping."
fi

echo "==> Configuring Starship..."
mkdir -p ~/.config
if [ ! -f ~/.config/starship.toml ]; then
    starship preset nerd-font-symbols -o ~/.config/starship.toml
else
    echo "~/.config/starship.toml already exists, leaving it alone."
fi

echo "==> Backing up ~/.zshrc to ~/.zshrc.bak..."
cp ~/.zshrc ~/.zshrc.bak 2>/dev/null || touch ~/.zshrc

echo "==> Adding plugins to Oh My Zsh plugins=(...) line..."
if grep -q "^plugins=(" ~/.zshrc; then
    for p in sudo command-not-found extract history-substring-search; do
        if ! grep "^plugins=(" ~/.zshrc | grep -qw "$p"; then
            sed -i "s/^plugins=(\(.*\))/plugins=(\1 $p)/" ~/.zshrc
        fi
    done
else
    echo 'plugins=(git sudo command-not-found extract history-substring-search)' >> ~/.zshrc
fi

echo "==> Appending rice config block to ~/.zshrc..."
if ! grep -q "# --- Rice additions ---" ~/.zshrc; then
cat >> ~/.zshrc << 'EOF'

# --- Rice additions ---
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

alias ls='eza --icons --group-directories-first'
alias ll='eza -l --icons --group-directories-first'
alias la='eza -la --icons --group-directories-first'
alias cat='bat'

eval "$(zoxide init zsh)"
alias cd='z'

source /usr/share/fzf/key-bindings.zsh
source /usr/share/fzf/completion.zsh
EOF
else
    echo "Rice block already present in ~/.zshrc, skipping."
fi

echo "==> Setting kitty terminal font (if kitty config exists)..."
if [ -f ~/.config/kitty/kitty.conf ]; then
    if ! grep -qE "^font_family\s+JetBrainsMono Nerd Font" ~/.config/kitty/kitty.conf; then
        echo 'font_family JetBrainsMono Nerd Font' >> ~/.config/kitty/kitty.conf
    fi
fi

echo ""
echo "Done! A backup of your old .zshrc is at ~/.zshrc.bak"
echo "Run: source ~/.zshrc   (or open a new terminal) to see the changes."

