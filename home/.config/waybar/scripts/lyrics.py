#!/usr/bin/env python3
"""Waybar module: current lyric line of whatever is playing (synced via LRCLIB), full lyrics in tooltip.
Follows playerctld (the most recently active player); empty when nothing plays or no lyrics exist."""
import json, os, re, subprocess, sys, hashlib, urllib.request, urllib.parse, html

CACHE = os.path.expanduser("~/.cache/waybar-lyrics")
os.makedirs(CACHE, exist_ok=True)
MAXLEN = 90
PLAYER = None  # None = playerctld / first player

def out(text="", tooltip="", cls="none"):
    print(json.dumps({"text": text, "tooltip": tooltip, "class": cls, "alt": cls}))
    sys.exit(0)

def pc(*args):
    try:
        return subprocess.run(["playerctl", *(["-p", PLAYER] if PLAYER else []), *args], capture_output=True, text=True, timeout=2).stdout.strip()
    except Exception:
        return ""

status = pc("status")
if status not in ("Playing", "Paused"):
    out()

meta = pc("metadata", "--format", "{{artist}}\t{{title}}\t{{album}}\t{{mpris:length}}")
try:
    artist, title, album, length = meta.split("\t")
    duration = int(int(length or 0) / 1_000_000)
except ValueError:
    out()
try:
    pos = float(pc("position") or 0)
except ValueError:
    pos = 0.0

key = hashlib.md5(f"{artist}|{title}|{album}".encode()).hexdigest()
path = os.path.join(CACHE, key + ".json")

if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
else:
    data = {"synced": "", "plain": ""}
    q = urllib.parse.urlencode({"artist_name": artist, "track_name": title,
                                "album_name": album, "duration": duration})
    try:
        req = urllib.request.Request("https://lrclib.net/api/get?" + q,
                                     headers={"User-Agent": "waybar-lyrics/1.0 (hyprland)"})
        with urllib.request.urlopen(req, timeout=6) as r:
            d = json.load(r)
            data = {"synced": d.get("syncedLyrics") or "", "plain": d.get("plainLyrics") or ""}
    except Exception:
        # fall back to fuzzy search without album/duration
        try:
            q = urllib.parse.urlencode({"artist_name": artist, "track_name": title})
            req = urllib.request.Request("https://lrclib.net/api/search?" + q,
                                         headers={"User-Agent": "waybar-lyrics/1.0 (hyprland)"})
            with urllib.request.urlopen(req, timeout=6) as r:
                res = json.load(r)
            best = next((x for x in res if x.get("syncedLyrics")), res[0] if res else None)
            if best:
                data = {"synced": best.get("syncedLyrics") or "", "plain": best.get("plainLyrics") or ""}
        except Exception:
            pass
    with open(path, "w") as f:
        json.dump(data, f)

def clip(s):
    s = s.strip()
    return s if len(s) <= MAXLEN else s[:MAXLEN - 1].rstrip() + "…"

head = f"{artist} — {title}"

if data["synced"]:
    lines = []
    for m in re.finditer(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)", data["synced"]):
        lines.append((int(m.group(1)) * 60 + float(m.group(2)), m.group(3).strip()))
    lines.sort()
    idx = -1
    for i, (t, _) in enumerate(lines):
        if t <= pos + 0.3:
            idx = i
        else:
            break
    current = lines[idx][1] if idx >= 0 else ""
    # tooltip: full lyrics with the current line highlighted
    tip = [f"<b>{html.escape(head)}</b>", ""]
    for i, (_, l) in enumerate(lines):
        l = html.escape(l) if l else "♪"
        tip.append(f"<span foreground='#3ae0ff'><b>{l}</b></span>" if i == idx else l)
    text = clip(current) if current else "♪"
    if status == "Paused":
        text = f"<i>{html.escape(text)}</i>"
    else:
        text = html.escape(text)
    out(text, "\n".join(tip), "synced" if status == "Playing" else "paused")
elif data["plain"]:
    tip = f"<b>{html.escape(head)}</b>\n\n" + html.escape(data["plain"])
    out("󰎆 lyrics", tip, "plain")
else:
    out("", f"{html.escape(head)}\n\nno lyrics found", "none")
