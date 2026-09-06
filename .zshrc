# ── oh-my-zsh ────────────────────────────────────────────────────
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME=""            # prompt is handled by starship
plugins=(git sudo command-not-found extract history-substring-search)
source "$ZSH/oh-my-zsh.sh"

# ── environment ──────────────────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"
export EDITOR="code --wait"

# ── plugins (pacman packages) ────────────────────────────────────
source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source /usr/share/fzf/key-bindings.zsh
source /usr/share/fzf/completion.zsh
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=#6b6b78"

# ── modern replacements ──────────────────────────────────────────
alias ls='eza --icons --group-directories-first'
alias ll='eza -l --icons --group-directories-first'
alias la='eza -la --icons --group-directories-first'
alias tree='eza --tree --icons'
alias cat='bat'
eval "$(zoxide init zsh)"
alias cd='z'

# ── personal aliases ─────────────────────────────────────────────
alias cl="clear"
alias tek="cd ~/epitech"
alias anime="ani-cli"
alias update="~/.config/waybar/scripts/update-now.sh"

# ── prompt + fetch ───────────────────────────────────────────────
eval "$(starship init zsh)"
[[ -o interactive && -z "$INSIDE_UPDATE_WINDOW" ]] && macchina

# dotfiles: bare repo in ~/.dotfiles, e.g. `dots status`, `dots add <file>`, `dots commit`
alias dots="git --git-dir=$HOME/.dotfiles --work-tree=$HOME"
