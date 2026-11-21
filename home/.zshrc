# ── oh-my-zsh ────────────────────────────────────────────────────
export ZSH="$HOME/.oh-my-zsh"
ZSH_DISABLE_COMPFIX=true  # skip the ~200 ms permission audit of completion dirs on every start
DISABLE_AUTO_UPDATE=true  # no update check at startup; the sigil update window (sigil-update-now) runs it
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
alias update="sigil-update-now"
alias rem="cd ~/Projects/remoters && claude"
alias orc="cd ~/Projects/orchastrate && orch up --open >/dev/null && claude --add-dir ~/Projects/remoters"

# ── prompt + fetch ───────────────────────────────────────────────
eval "$(starship init zsh)"
# sigil-shell palette: use its generated starship config while it exists
# (sigil mode), the plain one otherwise. Checked before every prompt.
sigil_starship() { [[ -f ~/.config/sigil/starship.toml ]] && export STARSHIP_CONFIG=~/.config/sigil/starship.toml || unset STARSHIP_CONFIG; }
precmd_functions=(sigil_starship $precmd_functions)
# macchina takes ~300 ms, so print the output cached by the previous shell and
# refresh the cache in the background (uptime/mem lag by one terminal open).
# Piped macchina positions rows with absolute ESC[row;1H, turned into newlines here.
if [[ -o interactive && -z "$INSIDE_UPDATE_WINDOW" ]]; then
  _mc_cache=${XDG_CACHE_HOME:-$HOME/.cache}/macchina.out
  if [[ -s $_mc_cache ]]; then print -r -- "$(<$_mc_cache)"; else macchina; fi
  ( macchina 2>/dev/null </dev/null | sed -E 's/\x1b\[[0-9]+;1H/\n/g' | sed '/^$/d' >| $_mc_cache.tmp \
      && mv -f $_mc_cache.tmp $_mc_cache ) &!
  unset _mc_cache
fi

# dotfiles: ~/dotfiles-and-scripts (configs are symlinks into it), e.g. `dots status`, `dots add -A`, `dots commit`, `dots push`
alias dots="git -C $HOME/dotfiles-and-scripts"

export PATH="$PATH:$HOME/.spicetify"  # spicetify (user install)
