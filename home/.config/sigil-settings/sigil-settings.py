#!/usr/bin/env python3
"""SIGIL // SETTINGS — control panel for the cybersigilism Hyprland rice.

Pages: Dashboard (live stats), Sounds (typewriter key sounds, packs), Power
(profile, brightness, night light, idle timers), Desktop (wallpaper gallery,
updates, services), Input (keyboard / touchpad via ~/.config/hypr/local.lua),
About (keys). Everything goes through the same scripts the bar and control
center use. `--page NAME` opens on a page.
"""
import os, re, sys, json, time, subprocess
os.environ.setdefault("GDK_DISABLE", "vulkan")  # GTK's Vulkan probe wakes the suspended dGPU (+2 s startup); GL is plenty
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk, GdkPixbuf

T_START = time.time()
HOME = os.path.expanduser("~")
CFG = os.path.join(HOME, ".config")
KS = os.path.join(CFG, "keysound")
KS_SH = os.path.join(KS, "keysound.sh")
KEEPAWAKE = os.path.join(CFG, "swaync", "keepawake.sh")
NIGHTLIGHT = os.path.join(CFG, "swaync", "nightlight.sh")
HYPRIDLE = os.path.join(CFG, "hypr", "hypridle.conf")
HYPRPAPER = os.path.join(CFG, "hypr", "hyprpaper.conf")
HYPRLOCK = os.path.join(CFG, "hypr", "hyprlock.conf")
HYPRSUNSET = os.path.join(CFG, "hypr", "hyprsunset.conf")
LOCAL_LUA = os.path.join(CFG, "hypr", "local.lua")
WALLS = os.path.join(HOME, "Pictures", "Wallpapers")
UPDATE_NOW = os.path.join(CFG, "waybar", "scripts", "update-now.sh")
RUNTIME = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
MONO = '"JetBrainsMono Nerd Font", monospace'

CSS = f"""
.sigil-brand {{ font-family: {MONO}; font-size: 0.8em; letter-spacing: 0.2em; color: @accent_color;
               text-shadow: 0 0 10px alpha(@accent_color, 0.55); }}
.sigil-mono {{ font-family: {MONO}; }}
.sigil-dim {{ color: alpha(@window_fg_color, 0.55); }}
.sigil-page-title {{ font-family: {MONO}; font-size: 1.1em; letter-spacing: 0.12em; }}
preferencesgroup > box > box > label.title, preferencesgroup label.heading {{
    font-family: {MONO}; letter-spacing: 0.1em; text-transform: uppercase; font-size: 0.78em;
    font-weight: normal; color: @accent_color; }}
.boxed-list {{ border: 1px solid @borders; border-radius: 0; }}
scale trough {{ min-height: 4px; }}
scale highlight {{ background: @accent_color; box-shadow: 0 0 6px alpha(@accent_color, 0.6); }}
scale slider {{ border-radius: 0; background: @accent_color; }}
switch:checked {{ background: @accent_color; }}
/* sidebar */
.sigil-sidebar {{ background: @sidebar_bg_color; border-right: 1px solid @borders; }}
.sigil-sidebar row {{ padding: 8px 14px; margin: 2px 6px; border-radius: 0; border-left: 2px solid transparent; }}
.sigil-sidebar row label {{ font-family: {MONO}; letter-spacing: 0.06em; font-size: 0.9em; }}
.sigil-sidebar row:selected {{ background: alpha(@accent_color, 0.08); border-left-color: @accent_color; }}
.sigil-sidebar row:selected label, .sigil-sidebar row:selected image {{ color: @accent_color; }}
.sigil-sidebar row:hover {{ background: alpha(@window_fg_color, 0.04); }}
/* dashboard */
.stat-card {{ background: @card_bg_color; border: 1px solid @borders; padding: 14px 16px; min-width: 150px; }}
.stat-card.alert {{ border-color: @warning_color; }}
.stat-card.bad {{ border-color: @error_color; }}
.stat-label {{ font-family: {MONO}; font-size: 0.7em; letter-spacing: 0.15em; color: alpha(@window_fg_color, 0.5); }}
.stat-value {{ font-family: {MONO}; font-size: 1.7em; color: @accent_color; text-shadow: 0 0 10px alpha(@accent_color, 0.45); }}
.stat-sub {{ font-family: {MONO}; font-size: 0.75em; color: alpha(@window_fg_color, 0.6); }}
.stat-bar trough {{ min-height: 3px; border-radius: 0; background: @borders; }}
.stat-bar progress {{ min-height: 3px; border-radius: 0; background: @accent_color; box-shadow: 0 0 6px alpha(@accent_color, 0.6); }}
.sigil-hero {{ font-family: {MONO}; font-size: 0.85em; color: alpha(@window_fg_color, 0.7); letter-spacing: 0.05em; }}
/* wallpaper gallery */
.wall-tile {{ border: 1px solid @borders; padding: 0; margin: 4px; background: @card_bg_color; }}
.wall-tile.current {{ border-color: @accent_color; box-shadow: 0 0 10px alpha(@accent_color, 0.5); }}
.wall-name {{ font-family: {MONO}; font-size: 0.72em; padding: 4px 6px; color: alpha(@window_fg_color, 0.7); }}
.key-cap {{ font-family: {MONO}; font-size: 0.8em; padding: 2px 8px; border: 1px solid @borders; background: @card_bg_color; color: @accent_color; }}
"""


# ── shell helpers ─────────────────────────────────────────────────────────────
def run(cmd, timeout=5):
    """Run a command (list or shell string) and return stdout, '' on failure."""
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def spawn(cmd):
    """Fire-and-forget, detached from the applet so it survives closing."""
    subprocess.Popen(cmd, shell=isinstance(cmd, str), start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def hypr_exec(command):
    spawn(["hyprctl", "dispatch", f'hl.dsp.exec_cmd("{command}")'])


def restart(proc, command=None):
    """Kill a daemon by exact process name and relaunch it through Hyprland."""
    run(["pkill", "-x", proc])
    GLib.timeout_add(300, lambda: (hypr_exec(command or proc), False)[1])


def run_async(cmd, done, timeout=30):
    """Run a command off the main loop; `done(stdout, returncode)` is called back on the GTK thread."""
    import threading
    def work():
        try:
            r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout)
            out, rc = (r.stdout + r.stderr).strip(), r.returncode
        except (subprocess.SubprocessError, OSError) as e:
            out, rc = str(e), 1
        GLib.idle_add(lambda: (done(out, rc), False)[1])
    threading.Thread(target=work, daemon=True).start()


def ask_password(parent, title, body, cb):
    """Adw.AlertDialog with a password entry; cb(password) on confirm."""
    dlg = Adw.AlertDialog(heading=title, body=body)
    entry = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="password")
    entry.set_margin_top(6); dlg.set_extra_child(entry)
    dlg.add_response("cancel", "Cancel"); dlg.add_response("ok", "Connect")
    dlg.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED); dlg.set_default_response("ok")
    entry.connect("activate", lambda *_: dlg.response("ok"))
    dlg.connect("response", lambda _d, r: cb(entry.get_text()) if r == "ok" else None)
    dlg.present(parent)


def snd(event):
    """UI sound from the active pack (no-op when system sounds are off)."""
    spawn([KS_SH, "play", event])


def wire_sounds(widget):
    """Walk a page's widget tree once and attach click/toggle sounds to buttons, switches and combos."""
    w = widget.get_first_child()
    while w is not None:
        if isinstance(w, Adw.SwitchRow):
            w.connect("notify::active", lambda r, _: snd("toggle-on" if r.get_active() else "toggle-off"))
        elif isinstance(w, Gtk.Switch):
            pass  # inside SwitchRow, handled above
        elif isinstance(w, Adw.ComboRow):
            w.connect("notify::selected", lambda *_: snd("click"))
        elif isinstance(w, Gtk.ToggleButton):
            w.connect("toggled", lambda b: snd("toggle-on" if b.get_active() else "toggle-off"))
        elif isinstance(w, Gtk.Button) and not isinstance(w, Gtk.ToggleButton):
            w.connect("clicked", lambda *_: snd("click"))
        wire_sounds(w)
        w = w.get_next_sibling()


def read(path, default=""):
    try:
        with open(path) as f:
            return f.read()
    except OSError:
        return default


# ── small widget helpers ──────────────────────────────────────────────────────
def scale_row(title, subtitle, value, on_change, lo=0, hi=100, step=1, fmt="{:.0f}%"):
    row = Adw.ActionRow(title=title, subtitle=subtitle)
    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, step)
    scale.set_value(value); scale.set_size_request(220, -1); scale.set_valign(Gtk.Align.CENTER)
    label = Gtk.Label(label=fmt.format(value), width_chars=7, xalign=1); label.add_css_class("sigil-mono")
    pending = {"id": 0}

    def changed(s):
        v = s.get_value(); label.set_label(fmt.format(v))
        if pending["id"]:
            GLib.source_remove(pending["id"])
        pending["id"] = GLib.timeout_add(150, lambda: (on_change(v), pending.update(id=0), False)[2])
    scale.connect("value-changed", changed)
    row.add_suffix(scale); row.add_suffix(label)
    row.scale = scale
    return row


def button_row(title, subtitle, *buttons):
    row = Adw.ActionRow(title=title, subtitle=subtitle)
    for label, cb, style in buttons:
        b = Gtk.Button(label=label, valign=Gtk.Align.CENTER)
        if style:
            b.add_css_class(style)
        b.connect("clicked", lambda _b, cb=cb: cb())
        row.add_suffix(b)
    return row


def spin(title, subtitle, value, lo, hi, step, digits=0):
    r = Adw.SpinRow.new_with_range(lo, hi, step)
    r.set_title(title); r.set_subtitle(subtitle); r.set_digits(digits); r.set_value(value)
    return r


class StatCard(Gtk.Box):
    """label / big value / sub line / thin bar"""
    def __init__(self, label, with_bar=True):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class("stat-card"); self.set_hexpand(True)
        l = Gtk.Label(label=label, xalign=0); l.add_css_class("stat-label"); self.append(l)
        self.value = Gtk.Label(label="—", xalign=0); self.value.add_css_class("stat-value"); self.append(self.value)
        self.sub = Gtk.Label(label="", xalign=0, ellipsize=3); self.sub.add_css_class("stat-sub"); self.append(self.sub)
        self.bar = None
        if with_bar:
            self.bar = Gtk.ProgressBar(); self.bar.add_css_class("stat-bar"); self.bar.set_margin_top(4); self.append(self.bar)

    def set(self, value, sub="", frac=None, state=""):
        self.value.set_label(value); self.sub.set_label(sub)
        if self.bar is not None and frac is not None:
            self.bar.set_fraction(max(0.0, min(1.0, frac)))
        for c in ("alert", "bad"):
            self.remove_css_class(c)
        if state:
            self.add_css_class(state)


# ── pages ─────────────────────────────────────────────────────────────────────
class DashboardPage(Adw.PreferencesPage):
    def __init__(self, toast, app):
        super().__init__(title="Dashboard", icon_name="utilities-system-monitor-symbolic")
        self.app = app
        hero = Adw.PreferencesGroup()
        kernel = run(["uname", "-r"]); host = run(["uname", "-n"])
        h = Gtk.Label(label=f"{host}  //  {os.environ.get('USER', '')}  //  linux {kernel}  //  hyprland", xalign=0)
        h.add_css_class("sigil-hero"); h.set_wrap(True); hero.add(h)
        self.add(hero)

        g = Adw.PreferencesGroup(title="Live")
        grid = Gtk.Grid(column_spacing=10, row_spacing=10, column_homogeneous=True)
        self.cpu, self.mem, self.bat, self.gpu = StatCard("CPU"), StatCard("MEMORY"), StatCard("BATTERY"), StatCard("dGPU", False)
        self.up, self.upd, self.prof, self.night = StatCard("UPTIME", False), StatCard("UPDATES", False), StatCard("PROFILE", False), StatCard("NIGHT LIGHT", False)
        for i, c in enumerate((self.cpu, self.mem, self.bat, self.gpu, self.up, self.upd, self.prof, self.night)):
            grid.attach(c, i % 4, i // 4, 1, 1)
        g.add(grid); self.add(g)

        g = Adw.PreferencesGroup(title="Quick actions")
        g.add(button_row("Lock", "loginctl lock-session", ("Lock now", lambda: spawn(["loginctl", "lock-session"]), None)))
        g.add(button_row("Session", "power menu / log out", ("Power menu", lambda: spawn(["wlogout"]), None)))
        g.add(button_row("Control center", "notifications and toggles", ("Open", lambda: spawn(["swaync-client", "-t", "-sw"]), None)))
        self.add(g)

        self.prev = None
        self.tick_id = 0
        self.paused = False
        app.profile_cache = app.profile_cache or run(["powerprofilesctl", "get"])
        app.night_cache = run([NIGHTLIGHT, "state"]) == "true"
        self.tick()

    @staticmethod
    def bat_dir():
        for d in sorted(os.listdir("/sys/class/power_supply")) if os.path.isdir("/sys/class/power_supply") else []:
            if d.startswith("BAT"):
                return "/sys/class/power_supply/" + d
        return None

    def tick(self):
        # CPU from /proc/stat delta
        f = read("/proc/stat").split("\n")[0].split()
        if len(f) > 5:
            vals = list(map(int, f[1:9])); idle = vals[3] + vals[4]; total = sum(vals)
            if self.prev:
                dt, di = total - self.prev[0], idle - self.prev[1]
                pct = 100 * (dt - di) / dt if dt else 0
                load = read("/proc/loadavg").split()[:3]
                self.cpu.set(f"{pct:.0f}%", "load " + " ".join(load), pct / 100, "alert" if pct > 85 else "")
            self.prev = (total, idle)
        # memory
        mi = {}
        for line in read("/proc/meminfo").splitlines():
            k, _, v = line.partition(":"); mi[k] = int(v.split()[0]) if v.split() else 0
        if mi.get("MemTotal"):
            used = mi["MemTotal"] - mi.get("MemAvailable", 0)
            self.mem.set(f"{used / 1048576:.1f} G", f"of {mi['MemTotal'] / 1048576:.1f} G · swap {(mi.get('SwapTotal', 0) - mi.get('SwapFree', 0)) / 1048576:.1f} G",
                         used / mi["MemTotal"], "alert" if used / mi["MemTotal"] > 0.9 else "")
        # battery
        b = self.bat_dir()
        if b:
            cap = int(read(b + "/capacity", "0") or 0); st = read(b + "/status").strip()
            pw = read(b + "/power_now", "0").strip()
            watts = f"{int(pw) / 1e6:.1f} W · " if pw.isdigit() and int(pw) else ""
            state = "bad" if cap <= 15 and st == "Discharging" else ("alert" if cap <= 30 and st == "Discharging" else "")
            self.bat.set(f"{cap}%", watts + st.lower(), cap / 100, state)
        # dGPU: ONLY power/runtime_status (a plain PM attribute; busy%/hwmon reads would wake the card),
        # and only every 5th tick (10 s). The card itself is detected once and cached.
        self.gpu_ticks = getattr(self, "gpu_ticks", 0) + 1
        if not hasattr(self, "gpu_card"):
            self.gpu_card = None
            for card in ("card1", "card0", "card2"):
                d = f"/sys/class/drm/{card}/device"
                if "amdgpu" in os.path.realpath(f"{d}/driver") and read(f"{d}/power/control").strip() == "auto":
                    self.gpu_card = card; break
        if self.gpu_ticks % 5 == 1:
            gs = read(f"/sys/class/drm/{self.gpu_card}/device/power/runtime_status").strip() if self.gpu_card else ""
            self.gpu.set(gs or "n/a", "runtime power state · every 10 s", state="" if gs != "active" else "alert")
        # uptime
        try:
            secs = float(read("/proc/uptime", "0").split()[0])
            self.up.set(f"{int(secs // 3600)}h {int(secs % 3600 // 60):02d}m", time.strftime("since %a %H:%M", time.localtime(time.time() - secs)))
        except (ValueError, IndexError):
            pass
        # updates cache
        try:
            d = json.loads(read(os.path.join(RUNTIME, "waybar-updates.json"), "{}"))
            n = re.sub(r"\D", "", d.get("text", "")) or "0"
            self.upd.set(n, d.get("tooltip", "").replace("\n", " · ") or "not checked", state="alert" if n != "0" else "")
        except ValueError:
            self.upd.set("?", "cache unreadable")
        # profile / night light (cheap: files + one fast script)
        prof = read("/sys/firmware/acpi/platform_profile").strip() or read(os.path.join(RUNTIME, "ppd-profile")).strip()
        self.prof.set(prof or self.app.profile_cache, "power-profiles-daemon")
        self.night.set("on" if self.app.night_cache else "off", "hyprsunset")
        self.tick_id = 0 if self.paused else GLib.timeout_add_seconds(2, self.tick)
        return False

    def pause(self):
        self.paused = True
        if self.tick_id:
            GLib.source_remove(self.tick_id); self.tick_id = 0

    def refresh(self):
        self.paused = False
        if not self.tick_id:
            self.prev = None; self.tick()


class SoundsPage(Adw.PreferencesPage):
    EVENTS = [("keys", "Keystrokes"), ("notify", "Notification"), ("notify-urgent", "Urgent"), ("lock", "Lock"), ("unlock", "Unlock"),
              ("shutter", "Shutter"), ("plug", "Plug"), ("unplug", "Unplug"), ("batt-low", "Battery low"),
              ("click", "Click"), ("toggle-on", "Toggle on"), ("toggle-off", "Toggle off"), ("open", "Open"), ("close", "Close")]

    def __init__(self, toast, app):
        super().__init__(title="Sound theme", icon_name="emblem-music-symbolic")
        self.toast = toast
        cfg = self.read_cfg()

        g = Adw.PreferencesGroup(title="Theme", description="One pack drives keystrokes, notifications and system events. "
                                                             "Packs live in ~/.config/keysound/packs/NAME/ as 23 WAV files.")
        self.packs = sorted(d for d in os.listdir(os.path.join(KS, "packs")) if os.path.isdir(os.path.join(KS, "packs", d)))
        self.pack = Adw.ComboRow(title="Active pack", subtitle="Switches live, no restart needed")
        self.pack.set_model(Gtk.StringList.new([self.pretty(p) for p in self.packs]))
        cur = cfg.get("pack", "cybersigil")
        self.pack.set_selected(self.packs.index(cur) if cur in self.packs else 0)
        self.pack.connect("notify::selected", self.on_pack)
        g.add(self.pack)
        prev = Adw.ActionRow(title="Preview", subtitle="Play each event from the selected pack")
        flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=5, column_spacing=4, row_spacing=4, valign=Gtk.Align.CENTER)
        for ev, label in self.EVENTS:
            b = Gtk.Button(label=label, css_classes=["flat", "sigil-mono"]); b.connect("clicked", lambda _b, e=ev: self.preview(e)); flow.append(b)
        prev.add_suffix(flow); g.add(prev)
        g.add(button_row("Pack files", "Open the folder or re-synthesise the built-in packs (a few seconds)",
                         ("Open folder", lambda: spawn(["xdg-open", os.path.join(KS, "packs")]), None), ("Regenerate", self.regen, None)))
        self.add(g)

        g = Adw.PreferencesGroup(title="Keystrokes", description="Typewriter clicks from a small daemon reading the keyboard.")
        self.enabled = Adw.SwitchRow(title="Key sounds", subtitle="Start or stop the daemon")
        self.enabled.set_active(run([KS_SH, "state"]) == "true")
        self.enabled.connect("notify::active", self.on_enabled)
        g.add(self.enabled)
        g.add(scale_row("Volume", "Mixer level for keystrokes", float(cfg.get("volume", 0.45)) * 100, lambda v: run([KS_SH, "volume", f"{v / 100:.2f}"])))
        self.add(g)

        g = Adw.PreferencesGroup(title="System sounds", description="Notifications, lock/unlock, screenshots, charger, low battery, and the clicks/toggles in this app, the bar and the control center. Silenced by do-not-disturb (except lock/unlock).")
        self.system = Adw.SwitchRow(title="System sounds")
        self.system.set_active(cfg.get("system", "true") != "false")
        self.system.connect("notify::active", lambda r, _: (run([KS_SH, "system", "on" if r.get_active() else "off"]), self.toast("System sounds " + ("on" if r.get_active() else "off"))))
        g.add(self.system)
        g.add(scale_row("Volume", "Level for system sounds", float(cfg.get("system_volume", 0.6)) * 100, lambda v: run([KS_SH, "system-volume", f"{v / 100:.2f}"])))
        self.add(g)

    def preview(self, ev):
        pack = self.packs[self.pack.get_selected()]
        if ev == "keys":
            spawn(["python3", os.path.join(KS, "keysoundd.py"), "--demo", "--pack", pack]); return
        f = os.path.join(KS, "packs", pack, ev + ".wav")
        vol = self.read_cfg().get("system_volume", "0.6")
        spawn(["pw-play", "--volume", vol, f])

    @staticmethod
    def pretty(name):
        return {"cybersigil": "Cybersigil (typewriter)", "animalese": "Animalese (Animal Crossing)"}.get(name, name.replace("-", " ").title())

    @staticmethod
    def read_cfg():
        out = {}
        for line in read(os.path.join(KS, "config")).splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1); out[k.strip()] = v.strip()
        return out

    def on_enabled(self, row, _):
        run([KS_SH, "start" if row.get_active() else "stop"])
        self.toast(f"Key sounds {'started' if row.get_active() else 'stopped'}")

    def on_pack(self, row, _):
        name = self.packs[row.get_selected()]
        run([KS_SH, "pack", name]); self.toast(f"Pack: {self.pretty(name)}")

    def regen(self):
        for p in ("cybersigil", "animalese"):
            run(["python3", os.path.join(KS, "gen-sounds.py"), "--pack", p], timeout=120)
        run([KS_SH, "pack", self.packs[self.pack.get_selected()]])
        self.toast("Packs regenerated")


class AudioPage(Adw.PreferencesPage):
    def __init__(self, toast, app):
        super().__init__(title="Audio", icon_name="audio-speakers-symbolic")
        self.toast = toast
        self.audio_group()

    # ── audio (wireplumber) ──
    @staticmethod
    def wp_nodes(kind):
        """[(id, name, is_default)] for 'Sinks' or 'Sources' from `wpctl status`."""
        out, nodes, grab = run(["wpctl", "status"]), [], False
        for line in out.splitlines():
            if re.search(rf"\b{kind}:", line):
                grab = True; continue
            if grab:
                m = re.match(r"\s*[│|]?\s*(\*?)\s*(\d+)\.\s+(.*?)\s+\[vol:", line)
                if m:
                    nodes.append((int(m.group(2)), m.group(3).strip(), m.group(1) == "*"))
                elif line.strip() in ("│", "") or "├─" in line:
                    if nodes:
                        break
        return nodes

    @staticmethod
    def wp_vol(target):
        m = re.search(r"Volume:\s*([\d.]+)(.*)", run(["wpctl", "get-volume", target]))
        return (float(m.group(1)) * 100 if m else 0.0, bool(m and "MUTED" in m.group(2)))

    def audio_group(self):
        g = Adw.PreferencesGroup(title="Devices and levels", description="Defaults from wireplumber; per-app control in the mixer.")
        for kind, target, title in (("Sinks", "@DEFAULT_AUDIO_SINK@", "Output"), ("Sources", "@DEFAULT_AUDIO_SOURCE@", "Input")):
            nodes = self.wp_nodes(kind)
            combo = Adw.ComboRow(title=title, subtitle="default device")
            combo.set_model(Gtk.StringList.new([n[1] for n in nodes] or ["none"]))
            cur = next((i for i, n in enumerate(nodes) if n[2]), 0); combo.set_selected(cur)
            combo.connect("notify::selected", lambda r, _, ns=nodes: ns and (run(["wpctl", "set-default", str(ns[r.get_selected()][0])]), self.toast(f"Default: {ns[r.get_selected()][1]}")))
            g.add(combo)
            vol, muted = self.wp_vol(target)
            row = scale_row(f"{title} volume", "muted" if muted else "", min(vol, 150), lambda v, t=target: run(["wpctl", "set-volume", t, f"{int(v)}%"]), lo=0, hi=150)
            mute = Gtk.ToggleButton(icon_name="audio-volume-muted-symbolic" if title == "Output" else "microphone-disabled-symbolic", valign=Gtk.Align.CENTER, active=muted, tooltip_text="Mute")
            mute.connect("toggled", lambda b, t=target, r=row: (run(["wpctl", "set-mute", t, "1" if b.get_active() else "0"]), r.set_subtitle("muted" if b.get_active() else "")))
            row.add_suffix(mute); g.add(row)
        g.add(button_row("Mixer", "per-app volumes, ports, profiles", ("Open pavucontrol", lambda: spawn(["pavucontrol"]), None)))
        self.add(g)


class PowerPage(Adw.PreferencesPage):
    def __init__(self, toast, app):
        super().__init__(title="Power", icon_name="battery-symbolic")
        self.toast, self.app = toast, app

        g = Adw.PreferencesGroup(title="Power profile")
        self.profiles = [l.strip().lstrip("* ").rstrip(":") for l in run(["powerprofilesctl", "list"]).splitlines()
                         if l.strip().endswith(":") and not l.startswith("    ")]
        self.profile = Adw.ComboRow(title="Profile", subtitle="power-profiles-daemon / amd-pstate-epp")
        self.profile.set_model(Gtk.StringList.new(self.profiles or ["unavailable"]))
        cur = run(["powerprofilesctl", "get"]); app.profile_cache = cur
        if cur in self.profiles:
            self.profile.set_selected(self.profiles.index(cur))
        self.profile.connect("notify::selected", self.on_profile)
        g.add(self.profile)
        self.awake = Adw.SwitchRow(title="Keep awake", subtitle="Inhibit idle dimming, lock and sleep")
        self.awake.set_active(run([KEEPAWAKE, "state"]) == "true")
        self.awake.connect("notify::active", lambda r, _: (run([KEEPAWAKE, "on" if r.get_active() else "off"]),
                                                            self.toast("Keep awake " + ("on" if r.get_active() else "off"))))
        g.add(self.awake)
        self.add(g)

        g = Adw.PreferencesGroup(title="Display")
        b = run(["brightnessctl", "-m"]).split(",")
        cur_b = float(b[3].rstrip("%")) if len(b) > 3 else 100
        g.add(scale_row("Brightness", "Panel backlight", cur_b, lambda v: run(["brightnessctl", "-q", "set", f"{int(v)}%"]), lo=1))
        self.add(g)

        g = Adw.PreferencesGroup(title="Night light",
                                 description="hyprsunset warms the screen on a schedule; the override switch lasts until the next scheduled change.")
        ns = self.read_sunset()
        self.sched = Adw.SwitchRow(title="Schedule", subtitle="Run hyprsunset at login and follow the times below")
        self.sched.set_active(ns["enabled"]); g.add(self.sched)
        self.night = Adw.SwitchRow(title="Night light now", subtitle="Manual override")
        app.night_cache = run([NIGHTLIGHT, "state"]) == "true"
        self.night.set_active(app.night_cache)
        self.night.connect("notify::active", self.on_night)
        g.add(self.night)
        self.temp_val, self.gamma_val, self.day_val = ns["temp"], ns["gamma"], ns["day"]
        g.add(scale_row("Night warmth", "Colour temperature at night (lower = warmer); previews live", ns["temp"],
                        self.preview_temp, lo=2500, hi=6000, step=100, fmt="{:.0f} K"))
        g.add(scale_row("Night brightness", "Gamma applied with the warm tint; previews live", ns["gamma"], self.preview_gamma, lo=40, hi=100, step=5))
        g.add(scale_row("Day warmth", "Daytime colour temperature; 6500 K = untouched", ns["day"], self.preview_day, lo=4000, hi=6500, step=100, fmt="{:.0f} K"))
        self.start = Adw.EntryRow(title="Evening start (HH:MM)"); self.start.set_text(ns["start"])
        self.end = Adw.EntryRow(title="Morning end (HH:MM)"); self.end.set_text(ns["end"])
        g.add(self.start); g.add(self.end)
        g.add(button_row("Apply schedule", "Write hyprsunset.conf and restart hyprsunset", ("Apply", self.apply_sunset, "suggested-action")))
        self.add(g)

        g = Adw.PreferencesGroup(title="Idle timers", description="Rewrites hypridle.conf and restarts hypridle. 0 disables a step.")
        t = self.read_idle()
        self.dim = spin("Dim after", "minutes", t["dim"] / 60, 0, 120, 0.5, 1)
        self.dim_level = spin("Dim level", "percent of full brightness", t["dim_level"], 1, 100, 5)
        self.lock = spin("Lock after", "minutes", t["lock"] / 60, 0, 240, 0.5, 1)
        self.off = spin("Screen off after", "minutes", t["off"] / 60, 0, 240, 0.5, 1)
        self.sleep = spin("Sleep after", "minutes, suspend", t["sleep"] / 60, 0, 480, 0.5, 1)
        for r in (self.dim, self.dim_level, self.lock, self.off, self.sleep):
            g.add(r)
        g.add(button_row("Apply", "Write the config and restart the idle daemon", ("Apply", self.apply_idle, "suggested-action")))
        self.add(g)

    def refresh(self):
        cur = run(["powerprofilesctl", "get"]); self.app.profile_cache = cur
        if cur in self.profiles and self.profile.get_selected() != self.profiles.index(cur):
            self.profile.handler_block_by_func(self.on_profile); self.profile.set_selected(self.profiles.index(cur)); self.profile.handler_unblock_by_func(self.on_profile)
        n = run([NIGHTLIGHT, "state"]) == "true"; self.app.night_cache = n
        if self.night.get_active() != n:
            self.night.handler_block_by_func(self.on_night); self.night.set_active(n); self.night.handler_unblock_by_func(self.on_night)

    def on_profile(self, row, _):
        if self.profiles:
            p = self.profiles[row.get_selected()]
            run(["powerprofilesctl", "set", p]); self.app.profile_cache = p; self.toast(f"Profile: {p}")

    def on_night(self, r, _):
        run([NIGHTLIGHT, "on" if r.get_active() else "off"]); self.app.night_cache = r.get_active()
        self.toast("Night light " + ("on" if r.get_active() else "off"))

    @staticmethod
    def read_sunset():
        d = {"start": "21:00", "end": "07:30", "temp": 4200, "gamma": 100, "day": 6500, "enabled": True}
        text = read(HYPRSUNSET)
        if not text:
            return d
        d["enabled"] = not re.search(r"^#\s*schedule\s*=\s*off", text, re.M)
        blocks = re.findall(r"profile\s*\{(.*?)\}", text, re.S)

        def temp_of(b):
            m = re.search(r"temperature\s*=\s*(\d+)", b)
            return int(m.group(1)) if m else 6500
        night = min(blocks, key=temp_of, default=None)
        for b in blocks:
            t = re.search(r"time\s*=\s*(\d+):(\d+)", b)
            if not t:
                continue
            hhmm = f"{int(t.group(1)):02d}:{int(t.group(2)):02d}"
            if b is night:
                d["start"], d["temp"] = hhmm, temp_of(b)
                g = re.search(r"gamma\s*=\s*(\d+)", b); d["gamma"] = int(g.group(1)) if g else 100
            else:
                d["end"], d["day"] = hhmm, temp_of(b)
        return d

    def preview_temp(self, v):
        self.temp_val = int(v)
        if self.night.get_active():
            run(["hyprctl", "hyprsunset", "temperature", str(self.temp_val)])

    def preview_gamma(self, v):
        self.gamma_val = int(v)
        if self.night.get_active():
            run(["hyprctl", "hyprsunset", "gamma", str(self.gamma_val)])

    def preview_day(self, v):
        self.day_val = int(v)
        if not self.night.get_active():
            run(["hyprctl", "hyprsunset", "identity"] if self.day_val >= 6500 else ["hyprctl", "hyprsunset", "temperature", str(self.day_val)])

    def apply_sunset(self):
        times = []
        for row in (self.start, self.end):
            m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", row.get_text())
            if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
                row.add_css_class("error"); self.toast("Time must be HH:MM"); return
            row.remove_css_class("error"); times.append(f"{int(m.group(1))}:{int(m.group(2)):02d}")
        enabled = self.sched.get_active()
        day = "    identity = true\n" if self.day_val >= 6500 else f"    temperature = {self.day_val}\n"
        night_gamma = f"    gamma = {self.gamma_val}\n" if self.gamma_val < 100 else ""
        with open(HYPRSUNSET, "w") as f:
            f.write("# hyprsunset schedule (generated by sigil-settings) - warm evenings, neutral by day\n"
                    "# manual override: ~/.config/swaync/nightlight.sh on|off|toggle\n"
                    f"# schedule = {'on' if enabled else 'off'}\nmax-gamma = 150\n\n"
                    f"profile {{\n    time = {times[1]}\n{day}}}\n\n"
                    f"profile {{\n    time = {times[0]}\n    temperature = {self.temp_val}\n{night_gamma}}}\n")
        run([NIGHTLIGHT, "reset"])
        if enabled:
            restart("hyprsunset")
        else:
            run(["hyprctl", "hyprsunset", "identity"]); run(["hyprctl", "hyprsunset", "gamma", "100"]); run(["pkill", "-x", "hyprsunset"])
        GLib.timeout_add(900, lambda: (self.night.set_active(run([NIGHTLIGHT, "state"]) == "true"), False)[1])
        self.toast("Night light schedule applied" if enabled else "Night light schedule disabled")

    @staticmethod
    def read_idle():
        t = {"dim": 120, "dim_level": 15, "lock": 300, "off": 600, "sleep": 630}
        for block in re.findall(r"listener\s*\{(.*?)\}", read(HYPRIDLE), re.S):
            m = re.search(r"timeout\s*=\s*(\d+)", block); cmd = re.search(r"on-timeout\s*=\s*(.*)", block)
            if not (m and cmd):
                continue
            secs, c = int(m.group(1)), cmd.group(1)
            if "brightnessctl" in c:
                t["dim"] = secs; lvl = re.search(r"set\s+(\d+)%", c)
                if lvl:
                    t["dim_level"] = int(lvl.group(1))
            elif "lock-session" in c:
                t["lock"] = secs
            elif "dpms" in c:
                t["off"] = secs
            elif "suspend" in c or "hibernate" in c:
                t["sleep"] = secs
        return t

    def apply_idle(self):
        dim, lock, off, sleep = (int(round(r.get_value() * 60)) for r in (self.dim, self.lock, self.off, self.sleep))
        level = int(self.dim_level.get_value())
        parts = ["general {", "    # plain hyprlock: a stale/hung hyprlock must not block re-locking", "    lock_cmd = hyprlock",
                 "    before_sleep_cmd = loginctl lock-session", "    after_sleep_cmd = hyprctl dispatch 'hl.dsp.dpms(\"on\")'",
                 "    inhibit_sleep = 3   # delay suspend until the lock screen is drawn", "}", "",
                 "# generated by sigil-settings; edit there or by hand (timeouts in seconds)"]
        if dim:
            parts += ["", "listener {", f"    timeout = {dim}", f"    on-timeout = brightnessctl -s set {level}%", "    on-resume = brightnessctl -r", "}"]
        if lock:
            parts += ["", "listener {", f"    timeout = {lock}", "    on-timeout = loginctl lock-session", "}"]
        if off:
            parts += ["", "listener {", f"    timeout = {off}", "    on-timeout = hyprctl dispatch 'hl.dsp.dpms(\"off\")'", "    on-resume = hyprctl dispatch 'hl.dsp.dpms(\"on\")'", "}"]
        if sleep:
            parts += ["", "listener {", f"    timeout = {sleep}", "    on-timeout = systemctl suspend", "}"]
        with open(HYPRIDLE, "w") as f:
            f.write("\n".join(parts) + "\n")
        restart("hypridle"); self.toast("hypridle restarted with new timers")


class DesktopPage(Adw.PreferencesPage):
    def __init__(self, toast, app):
        super().__init__(title="Desktop", icon_name="preferences-desktop-wallpaper-symbolic")
        self.toast = toast
        self.wall = self.read_wallpaper()

        g = Adw.PreferencesGroup(title="Wallpaper", description=f"Images in {WALLS.replace(HOME, '~')}. Click a tile to apply; hyprlock's background follows.")
        self.flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=4, min_children_per_line=2,
                                column_spacing=6, row_spacing=6, homogeneous=True)
        self.tiles = {}
        self.fill_gallery()
        g.add(self.flow)
        g.add(button_row("Other image", "Pick any file; it is copied into the wallpaper folder", ("Choose…", self.pick_wallpaper, None)))
        self.add(g)

        g = Adw.PreferencesGroup(title="Updates")
        self.upd = button_row("Pending packages", self.update_text(),
                              ("Check now", self.check_updates, None), ("Update", lambda: spawn([UPDATE_NOW]), "suggested-action"))
        g.add(self.upd); self.add(g)

        g = Adw.PreferencesGroup(title="Services", description="Restart a piece of the desktop without logging out.")
        for title, sub, cb in (
            ("Waybar", "status bar", lambda: restart("waybar")),
            ("SwayNC", "notifications + control center (reloads config and style)", lambda: (run(["swaync-client", "-R"]), run(["swaync-client", "-rs"]))),
            ("hypridle", "idle daemon", lambda: restart("hypridle")),
            ("hyprpaper", "wallpaper daemon", lambda: restart("hyprpaper")),
            ("hyprsunset", "night light daemon", lambda: restart("hyprsunset")),
            ("Key sounds", "typewriter daemon", lambda: run([KS_SH, "restart"])),
            ("Hyprland config", "hyprctl reload", lambda: run(["hyprctl", "reload"])),
            ("Settings app", "this window (resident); reloads its code", lambda: spawn("sh -c 'python3 ~/.config/sigil-settings/sigil-settings.py --quit; sleep 1; python3 ~/.config/sigil-settings/sigil-settings.py --hidden'")),
        ):
            g.add(button_row(title, sub, ("Restart", lambda cb=cb, t=title: (cb(), self.toast(f"{t} restarted")), None)))
        self.add(g)

        g = Adw.PreferencesGroup(title="Dotfiles", description="~/dotfiles-and-scripts — configs are symlinks into it; a weekly timer commits and pushes.")
        st = run(["git", "-C", os.path.join(HOME, "dotfiles-and-scripts"), "status", "--porcelain"])
        self.dots = button_row("Repository", f"{len(st.splitlines())} uncommitted change(s)" if st else "clean",
                               ("Sync now", self.sync_dots, "suggested-action"), ("Open", lambda: spawn(["xdg-open", os.path.join(HOME, "dotfiles-and-scripts")]), None))
        g.add(self.dots); self.add(g)

    # wallpaper
    @staticmethod
    def read_wallpaper():
        m = re.search(r"^\s*path\s*=\s*(.+)$", read(HYPRPAPER), re.M)
        return m.group(1).strip() if m else ""

    def fill_gallery(self):
        for child in list(self.tiles.values()):
            self.flow.remove(child)
        self.tiles.clear()
        files = sorted(f for f in (os.listdir(WALLS) if os.path.isdir(WALLS) else []) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and not f.endswith("_raw.png"))
        for f in files:
            path = os.path.join(WALLS, f)
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 200, 112, True)
            except GLib.Error:
                continue
            pic = Gtk.Picture.new_for_pixbuf(pb); pic.set_size_request(200, 112); pic.set_content_fit(Gtk.ContentFit.COVER)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); box.add_css_class("wall-tile")
            box.append(pic)
            name = Gtk.Label(label=os.path.splitext(f)[0], xalign=0, ellipsize=3); name.add_css_class("wall-name"); box.append(name)
            btn = Gtk.Button(child=box); btn.add_css_class("flat"); btn.set_tooltip_text(path)
            btn.connect("clicked", lambda _b, p=path: self.apply_wallpaper(p))
            if os.path.realpath(path) == os.path.realpath(self.wall):
                box.add_css_class("current")
            self.tiles[path] = btn; self.flow.append(btn); btn.connect("clicked", lambda *_: snd("click"))

    def pick_wallpaper(self):
        dlg = Gtk.FileDialog(title="Choose wallpaper")
        f = Gtk.FileFilter(); f.set_name("Images"); f.add_mime_type("image/*")
        fl = Gio.ListStore.new(Gtk.FileFilter); fl.append(f); dlg.set_filters(fl)
        dlg.open(self.get_root(), None, self.on_picked)

    def on_picked(self, dlg, res):
        try:
            path = dlg.open_finish(res).get_path()
        except GLib.Error:
            return
        os.makedirs(WALLS, exist_ok=True)
        dest = os.path.join(WALLS, os.path.basename(path))
        if os.path.realpath(path) != os.path.realpath(dest):
            import shutil; shutil.copy2(path, dest)
        self.apply_wallpaper(dest); self.fill_gallery()

    def apply_wallpaper(self, path):
        with open(HYPRPAPER, "w") as f:
            f.write("wallpaper {\n    monitor =\n    path = %s\n    fit_mode = cover\n}\nsplash = false\n" % path)
        text = read(HYPRLOCK)
        if self.wall and self.wall in text:
            with open(HYPRLOCK, "w") as f:
                f.write(text.replace(self.wall, path))
        self.wall = path
        for p, btn in self.tiles.items():
            box = btn.get_child()
            (box.add_css_class if os.path.realpath(p) == os.path.realpath(path) else box.remove_css_class)("current")
        restart("hyprpaper"); self.toast("Wallpaper applied")

    # updates / dotfiles
    @staticmethod
    def update_text():
        try:
            d = json.loads(read(os.path.join(RUNTIME, "waybar-updates.json"), "{}"))
            n = d.get("text", "").strip()
            return f"{n} pending" if n else "up to date"
        except ValueError:
            return "not checked yet"

    def check_updates(self):
        run(["pkill", "-RTMIN+9", "-x", "waybar"]); self.toast("Checking for updates…")
        GLib.timeout_add(8000, lambda: (self.upd.set_subtitle(self.update_text()), False)[1])

    def sync_dots(self):
        out = run([os.path.join(HOME, ".local", "bin", "dots-sync")], timeout=60)
        self.dots.set_subtitle(out.replace("\n", " · ") or "nothing to do"); self.toast("Dotfiles synced")


class InputPage(Adw.PreferencesPage):
    """Keyboard / mouse / touchpad overrides written to ~/.config/hypr/local.lua (loaded with pcall, so a bad
    write can never take the session down). The main hyprland.lua is never touched."""
    def __init__(self, toast, app):
        super().__init__(title="Input", icon_name="input-mouse-symbolic")
        self.toast = toast
        v = self.current()
        g = Adw.PreferencesGroup(title="Keyboard", description="Layout stays in hyprland.lua (fr / azerty).")
        self.rate = spin("Repeat rate", "keys per second while held", v["repeat_rate"], 5, 80, 1)
        self.delay = spin("Repeat delay", "ms before repeat starts", v["repeat_delay"], 100, 1500, 25)
        g.add(self.rate); g.add(self.delay); self.add(g)

        g = Adw.PreferencesGroup(title="Mouse")
        self.sens = scale_row("Sensitivity", "libinput accel bias (-1 … 1)", v["sensitivity"], lambda _v: None, lo=-1, hi=1, step=0.05, fmt="{:+.2f}")
        g.add(self.sens); self.add(g)

        g = Adw.PreferencesGroup(title="Touchpad")
        self.natural = Adw.SwitchRow(title="Natural scrolling"); self.natural.set_active(v["natural_scroll"])
        self.tap = Adw.SwitchRow(title="Tap to click"); self.tap.set_active(v["tap_to_click"])
        self.dwt = Adw.SwitchRow(title="Disable while typing"); self.dwt.set_active(v["disable_while_typing"])
        self.clickfinger = Adw.SwitchRow(title="Clickfinger", subtitle="2 fingers = right click, 3 = middle (instead of button areas)")
        self.clickfinger.set_active(v["clickfinger_behavior"])
        self.tp_scroll = scale_row("Scroll speed", "touchpad scroll factor", v["scroll_factor"], lambda _v: None, lo=0.2, hi=3, step=0.1, fmt="{:.1f}x")
        for r in (self.natural, self.tap, self.dwt, self.clickfinger, self.tp_scroll):
            g.add(r)
        g.add(button_row("Apply", "Write local.lua and reload Hyprland", ("Apply", self.apply, "suggested-action"),
                         ("Reset", self.reset, "destructive-action")))
        self.add(g)

    @staticmethod
    def opt(name, default):
        out = run(["hyprctl", "getoption", name]).split("\n")[0]
        m = re.search(r"(int|float|bool|str):\s*(.+)", out)
        if not m:
            return default
        t, val = m.group(1), m.group(2).strip()
        return {"int": int, "float": float, "bool": lambda s: s == "true", "str": str}[t](val) if t != "bool" else val == "true"

    def current(self):
        return {"repeat_rate": self.opt("input:repeat_rate", 25), "repeat_delay": self.opt("input:repeat_delay", 600),
                "sensitivity": self.opt("input:sensitivity", 0.0), "natural_scroll": self.opt("input:touchpad:natural_scroll", True),
                "tap_to_click": self.opt("input:touchpad:tap_to_click", True), "disable_while_typing": self.opt("input:touchpad:disable_while_typing", True),
                "clickfinger_behavior": self.opt("input:touchpad:clickfinger_behavior", False), "scroll_factor": self.opt("input:touchpad:scroll_factor", 1.0)}

    def apply(self):
        lua = ("-- generated by sigil-settings (Input page); loaded from hyprland.lua with pcall(dofile). Safe to delete.\n"
               "hl.config({ input = {\n"
               f"    repeat_rate = {int(self.rate.get_value())}, repeat_delay = {int(self.delay.get_value())},\n"
               f"    sensitivity = {self.sens.scale.get_value():.2f},\n"
               "    touchpad = {\n"
               f"        natural_scroll = {str(self.natural.get_active()).lower()}, tap_to_click = {str(self.tap.get_active()).lower()},\n"
               f"        disable_while_typing = {str(self.dwt.get_active()).lower()}, clickfinger_behavior = {str(self.clickfinger.get_active()).lower()},\n"
               f"        scroll_factor = {self.tp_scroll.scale.get_value():.2f},\n"
               "    },\n} })\n")
        with open(LOCAL_LUA, "w") as f:
            f.write(lua)
        run(["hyprctl", "reload"])
        err = run(["hyprctl", "configerrors"])
        self.toast("Input settings applied" if not err.strip() else "Hyprland reported a config error, see hyprctl configerrors")

    def reset(self):
        try:
            os.remove(LOCAL_LUA)
        except OSError:
            pass
        run(["hyprctl", "reload"]); self.toast("local.lua removed, back to hyprland.lua defaults")


class WifiPage(Adw.PreferencesPage):
    """Wi-Fi via nmcli. Scans and connects run in threads."""
    def __init__(self, toast, app):
        super().__init__(title="Wi-Fi", icon_name="network-wireless-symbolic")
        self.toast = toast
        self.wifi_dev = next((l.split(":")[0] for l in run(["nmcli", "-t", "-f", "DEVICE,TYPE", "dev"]).splitlines() if l.endswith(":wifi")), "wlan0")

        g = Adw.PreferencesGroup(title="Wi-Fi")
        self.wifi_sw = Adw.SwitchRow(title="Wi-Fi", subtitle=self.wifi_dev)
        self.wifi_sw.set_active(run(["nmcli", "radio", "wifi"]) == "enabled")
        self.wifi_sw.connect("notify::active", lambda r, _: (run(["nmcli", "radio", "wifi", "on" if r.get_active() else "off"]),
                                                              GLib.timeout_add(1500, lambda: (self.scan_wifi(), False)[1])))
        g.add(self.wifi_sw); self.add(g)

        g = Adw.PreferencesGroup(title="Remote access", description="Tailscale: private network between your devices, works from anywhere; SSH goes over it.")
        self.ts_row = Adw.ActionRow(title="Tailscale", subtitle=self.ts_status())
        b = Gtk.Button(label="Copy ssh command", valign=Gtk.Align.CENTER); b.connect("clicked", lambda *_: self.copy_ts()); self.ts_row.add_suffix(b)
        g.add(self.ts_row); self.add(g)

        self.wifi_group = Adw.PreferencesGroup(title="Networks")
        b = Gtk.Button(label="Rescan", valign=Gtk.Align.CENTER); b.connect("clicked", lambda *_: self.scan_wifi(rescan=True))
        self.wifi_group.set_header_suffix(b)
        self.wifi_rows = []
        self.add(self.wifi_group)
        self.scan_wifi()


    def refresh(self):
        self.ts_row.set_subtitle(self.ts_status()); self.scan_wifi()

    @staticmethod
    def ts_info():
        """(state, ip, magicdns name, peer count) from tailscale; state '' when not installed/running"""
        raw = run(["tailscale", "status", "--json"], timeout=4)
        try:
            d = json.loads(raw)
        except ValueError:
            return ("", "", "", 0)
        me = d.get("Self", {}) or {}
        ip = next((a for a in me.get("TailscaleIPs", []) if "." in a), "")
        name = (me.get("DNSName") or "").rstrip(".")
        online = sum(1 for p in (d.get("Peer") or {}).values() if p.get("Online"))
        return (d.get("BackendState", ""), ip, name, online)

    def ts_status(self):
        st, ip, name, online = self.ts_info()
        if not st:
            return "not installed or not running (sudo pacman -S tailscale; sudo systemctl enable --now tailscaled; sudo tailscale up --ssh)"
        if st != "Running":
            return f"{st.lower()} · run: sudo tailscale up --ssh"
        return f"connected · {ip}" + (f" · {name.split('.')[0]}" if name else "") + f" · {online} other device(s) online"

    def copy_ts(self):
        st, ip, name, _ = self.ts_info()
        target = name.split(".")[0] if name else ip
        if target:
            subprocess.run(["wl-copy"], input=f"ssh {os.environ.get('USER', 'kali')}@{target}", text=True); self.toast(f"Copied: ssh kali@{target}")
        else:
            self.toast("Tailscale is not connected")

    # ── wifi ──
    def scan_wifi(self, rescan=False):
        args = ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,BSSID", "dev", "wifi", "list"] + (["--rescan", "yes"] if rescan else [])
        self.wifi_group.set_description("scanning…" if rescan else None)
        run_async(args, self.fill_wifi, timeout=25)

    def fill_wifi(self, out, rc):
        for r in self.wifi_rows:
            self.wifi_group.remove(r)
        self.wifi_rows.clear()
        active = {l.split(":")[0] for l in run(["nmcli", "-t", "-f", "NAME,DEVICE", "con", "show", "--active"]).splitlines() if l.endswith(":" + self.wifi_dev)}
        known = {l.split(":")[0] for l in run(["nmcli", "-t", "-f", "NAME,TYPE", "con", "show"]).splitlines() if l.endswith("802-11-wireless")}
        seen, nets = set(), []
        for line in out.splitlines():
            parts = line.replace("\\:", "\x00").split(":")
            if len(parts) < 3:
                continue
            ssid, sig, sec = parts[0], parts[1], parts[2]
            if not ssid or ssid in seen:
                continue
            seen.add(ssid); nets.append((ssid, int(sig or 0), sec))
        nets.sort(key=lambda n: (n[0] not in active, -n[1]))
        self.wifi_group.set_description(f"{len(nets)} network(s) · {self.wifi_dev}" if nets else ("Wi-Fi is off" if not self.wifi_sw.get_active() else "nothing found"))
        for ssid, sig, sec in nets:
            row = Adw.ActionRow(title=ssid, subtitle=f"{sig}%  ·  {sec or 'open'}" + ("  ·  saved" if ssid in known and ssid not in active else ""))
            icon = "network-wireless-signal-excellent-symbolic" if sig > 75 else "network-wireless-signal-good-symbolic" if sig > 50 else "network-wireless-signal-ok-symbolic" if sig > 25 else "network-wireless-signal-weak-symbolic"
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            if ssid in active:
                row.add_css_class("accent"); row.set_title(f"{ssid}  ✓")
                b = Gtk.Button(label="Disconnect", valign=Gtk.Align.CENTER); b.connect("clicked", lambda *_: self.wifi_cmd(["nmcli", "dev", "disconnect", self.wifi_dev], "Disconnected"))
                row.add_suffix(b)
            else:
                b = Gtk.Button(label="Connect", valign=Gtk.Align.CENTER, css_classes=["suggested-action"])
                b.connect("clicked", lambda _b, ss=ssid, sc=sec, kn=(ssid in known): self.connect_wifi(ss, sc, kn)); row.add_suffix(b)
                if ssid in known:
                    f = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Forget network", css_classes=["flat"])
                    f.connect("clicked", lambda _b, ss=ssid: self.wifi_cmd(["nmcli", "con", "delete", "id", ss], f"Forgot {ss}")); row.add_suffix(f)
            self.wifi_group.add(row); self.wifi_rows.append(row); wire_sounds(row)

    def connect_wifi(self, ssid, sec, known):
        if known or not sec:
            self.wifi_cmd(["nmcli", "con", "up", "id", ssid] if known else ["nmcli", "dev", "wifi", "connect", ssid], f"Connected to {ssid}")
        else:
            ask_password(self.get_root(), ssid, f"{sec} network", lambda pw: self.wifi_cmd(["nmcli", "dev", "wifi", "connect", ssid, "password", pw], f"Connected to {ssid}"))

    def wifi_cmd(self, cmd, ok_msg):
        self.toast("Working…")
        run_async(cmd, lambda out, rc: (self.toast(ok_msg if rc == 0 else out.splitlines()[-1][:90] if out else "failed"), self.scan_wifi()), timeout=45)

class BluetoothPage(Adw.PreferencesPage):
    """Bluetooth via bluetoothctl. Scans, pairing and connects run in threads."""
    def __init__(self, toast, app):
        super().__init__(title="Bluetooth", icon_name="bluetooth-symbolic")
        self.toast = toast
        g = Adw.PreferencesGroup(title="Bluetooth")
        self.bt_sw = Adw.SwitchRow(title="Bluetooth", subtitle="adapter power")
        self.bt_sw.set_active("Powered: yes" in run(["bluetoothctl", "show"]))
        self.bt_sw.connect("notify::active", lambda r, _: (run(["bluetoothctl", "power", "on" if r.get_active() else "off"]),
                                                            GLib.timeout_add(800, lambda: (self.list_bt(), False)[1])))
        g.add(self.bt_sw); self.add(g)

        self.bt_group = Adw.PreferencesGroup(title="Devices")
        self.bt_scan_btn = Gtk.Button(label="Scan 8 s", valign=Gtk.Align.CENTER); self.bt_scan_btn.connect("clicked", lambda *_: self.scan_bt())
        self.bt_group.set_header_suffix(self.bt_scan_btn)
        self.bt_rows = []
        self.add(self.bt_group)
        self.list_bt()

    def refresh(self):
        self.list_bt()

    # ── bluetooth ──
    def list_bt(self):
        for r in self.bt_rows:
            self.bt_group.remove(r)
        self.bt_rows.clear()
        if not self.bt_sw.get_active():
            self.bt_group.set_description("Bluetooth is off"); return
        devs = []
        for line in run(["bluetoothctl", "devices"]).splitlines():
            m = re.match(r"Device ([0-9A-F:]{17}) (.*)", line)
            if m:
                info = run(["bluetoothctl", "info", m.group(1)])
                devs.append((m.group(2), m.group(1), "Connected: yes" in info, "Paired: yes" in info, "Trusted: yes" in info))
        devs.sort(key=lambda d: (not d[2], not d[3], d[0].lower()))
        self.bt_group.set_description(f"{len(devs)} device(s)" if devs else "no devices known; scan to find some")
        for name, mac, conn, paired, trusted in devs:
            row = Adw.ActionRow(title=f"{name}  ✓" if conn else name, subtitle=f"{mac}  ·  " + ("connected" if conn else "paired" if paired else "seen, not paired"))
            row.add_prefix(Gtk.Image.new_from_icon_name("bluetooth-active-symbolic" if conn else "bluetooth-symbolic"))
            if conn:
                b = Gtk.Button(label="Disconnect", valign=Gtk.Align.CENTER); b.connect("clicked", lambda _b, m=mac: self.bt_cmd(["bluetoothctl", "disconnect", m], "Disconnected"))
            elif paired:
                b = Gtk.Button(label="Connect", valign=Gtk.Align.CENTER, css_classes=["suggested-action"]); b.connect("clicked", lambda _b, m=mac: self.bt_cmd(["bluetoothctl", "connect", m], f"Connected {name}"))
            else:
                b = Gtk.Button(label="Pair", valign=Gtk.Align.CENTER, css_classes=["suggested-action"])
                b.connect("clicked", lambda _b, m=mac, n=name: self.bt_cmd(f"bluetoothctl pair {m} && bluetoothctl trust {m} && bluetoothctl connect {m}", f"Paired {n}", 40))
            row.add_suffix(b)
            f = Gtk.Button(icon_name="user-trash-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Forget device", css_classes=["flat"])
            f.connect("clicked", lambda _b, m=mac, n=name: self.bt_cmd(["bluetoothctl", "remove", m], f"Forgot {n}")); row.add_suffix(f)
            self.bt_group.add(row); self.bt_rows.append(row); wire_sounds(row)

    def scan_bt(self):
        self.bt_scan_btn.set_sensitive(False); self.bt_group.set_description("scanning for 8 s…")
        run_async(["bluetoothctl", "--timeout", "8", "scan", "on"], lambda out, rc: (self.bt_scan_btn.set_sensitive(True), self.list_bt()), timeout=20)

    def bt_cmd(self, cmd, ok_msg, timeout=20):
        self.toast("Working…")
        run_async(cmd, lambda out, rc: (self.toast(ok_msg if rc == 0 else (out.splitlines()[-1][:90] if out else "failed")), self.list_bt()), timeout=timeout)



class AboutPage(Adw.PreferencesPage):
    KEYS = [("SUPER + T", "terminal"), ("SUPER + R", "launcher"), ("SUPER + E", "files"), ("SUPER + B", "browser"),
            ("SUPER + N", "control center"), ("SUPER + I", "this app"), ("SUPER + L", "lock"), ("SUPER + Q", "close window"),
            ("SUPER + V", "float"), ("SUPER + SHIFT + V", "clipboard history"), ("SUPER + O", "emoji"), ("SUPER + P", "pop-out (pin)"),
            ("SUPER + F", "fullscreen"), ("SUPER + 1..9", "workspaces"), ("SUPER + S / D / M", "scratch · discord · spotify"),
            ("Print", "screenshot → satty"), ("SUPER + Print", "region → clipboard")]

    def __init__(self, toast, app):
        super().__init__(title="About", icon_name="help-about-symbolic")
        dbg = os.environ.get("SIGIL_ABOUT", "keys,sigil").split(",")
        if "keys" in dbg:
            g = Adw.PreferencesGroup(title="Keys")
            for k, d in self.KEYS:
                row = Adw.ActionRow(title=d)
                mode = os.environ.get("SIGIL_CAP", "css")
                if mode == "button":
                    cap = Gtk.Button(label=k); cap.add_css_class("flat"); cap.add_css_class("key-cap"); cap.set_can_focus(False)
                else:
                    cap = Gtk.Label(label=k)
                    if mode == "css":
                        cap.add_css_class("key-cap")
                cap.set_valign(Gtk.Align.CENTER); row.add_suffix(cap); g.add(row)
            self.add(g)
        if "sigil" in dbg:
            ver = run(["hyprctl", "version"]).split()
            g = Adw.PreferencesGroup(title="Sigil")
            for t, s in (("Palette", "cherenkov blue · plasmatic purple · snooze pink · communication red · wavelength green · infrared · phosphorus amber"),
                         ("Stack", f"hyprland {ver[1] if len(ver) > 1 else ''} · waybar · swaync · hyprlock · kitty · rofi · zsh + starship"),
                         ("Repo", "github.com/volcinator8000/dotfiles-and-scripts")):
                g.add(Adw.ActionRow(title=t, subtitle=s))
            self.add(g)


# ── application ───────────────────────────────────────────────────────────────
PAGES = [("dashboard", "Dashboard", "utilities-system-monitor-symbolic", DashboardPage),
         ("wifi", "Wi-Fi", "network-wireless-symbolic", WifiPage),
         ("bluetooth", "Bluetooth", "bluetooth-symbolic", BluetoothPage),
         ("audio", "Audio", "audio-speakers-symbolic", AudioPage),
         ("sounds", "Sound theme", "emblem-music-symbolic", SoundsPage),
         ("power", "Power", "battery-symbolic", PowerPage),
         ("desktop", "Desktop", "preferences-desktop-wallpaper-symbolic", DesktopPage),
         ("input", "Input", "input-mouse-symbolic", InputPage),
         ("about", "About", "help-about-symbolic", AboutPage)]


class App(Adw.Application):
    """Resident: the window is built once and hidden on close; `--toggle` shows/hides, `--page X` jumps,
    `--hidden` starts without showing (autostart), `--quit` exits. GApplication routes a second launch here."""
    def __init__(self):
        super().__init__(application_id="io.sigil.Settings", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.profile_cache, self.night_cache = "", False
        self.win, self.pages, self.holders, self.sidebar = None, {}, {}, None

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.hold()  # stay alive with the window hidden

    def do_command_line(self, cmdline):
        args = cmdline.get_arguments()[1:]
        if os.environ.get("SIGIL_TIMING"):
            print(f"command_line {args} visible={self.win.get_visible() if self.win else None} t={time.time() - T_START:.2f}s", file=sys.stderr)
        if "--quit" in args:
            self.quit(); return 0
        if self.win is None:
            self.build()
        if "--page" in args:
            self.select_page(args[args.index("--page") + 1])
        if "--hidden" in args and not self.win.get_visible():
            return 0
        if "--toggle" in args and self.win.get_visible() and self.win.is_active():
            self.hide_win(); return 0
        self.show_win(); return 0

    def do_activate(self):
        if self.win is None:
            self.build()
        self.show_win()

    # ── show / hide ──
    def show_win(self):
        if not self.win.get_visible():
            snd("open")
        self.win.present()
        cur = self.stack.get_visible_child_name()
        page = self.pages.get(cur)
        if page is not None and hasattr(page, "refresh"):
            page.refresh()

    def hide_win(self):
        if self.win.get_visible():
            snd("close")
        self.win.set_visible(False)
        if "dashboard" in self.pages:
            self.pages["dashboard"].pause()

    def select_page(self, name):
        idx = next((i for i, p in enumerate(PAGES) if p[0] == name and p[0] in self.holders), None)
        if idx is not None:
            self.sidebar.select_row(self.sidebar.get_row_at_index(idx))

    def build(self):
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        if not os.environ.get("SIGIL_NOCSS"):
            prov = Gtk.CssProvider(); prov.load_from_string(CSS)
            Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        win = Adw.ApplicationWindow(application=self, title="SIGIL // SETTINGS", default_width=980, default_height=680)
        self.win = win
        toasts = Adw.ToastOverlay()
        toast = lambda msg: toasts.add_toast(Adw.Toast(title=msg, timeout=2))

        stack = Adw.ViewStack(); self.stack = stack
        only = os.environ.get("SIGIL_ONLY", "").split(",") if os.environ.get("SIGIL_ONLY") else None  # debug: subset
        pages, holders = self.pages, self.holders
        for name, title, icon, cls in PAGES:
            if only and name not in only:
                continue
            holder = Gtk.Box(); holders[name] = holder  # placeholder, filled on first visit
            stack.add_titled_with_icon(holder, name, title, icon)

        def ensure(name):
            if name in pages or name not in holders:
                return False
            cls = next(c for n, _, _, c in PAGES if n == name)
            pages[name] = cls(toast, self)
            pages[name].set_hexpand(True); pages[name].set_vexpand(True)
            holders[name].append(pages[name])
            wire_sounds(pages[name])
            return True

        sidebar = Gtk.ListBox(); sidebar.add_css_class("navigation-sidebar"); sidebar.add_css_class("sigil-sidebar")
        sidebar.set_size_request(190, -1); self.sidebar = sidebar
        for name, title, icon, _ in PAGES:
            if name not in holders:
                continue
            row = Gtk.ListBoxRow(); row.page = name
            box = Gtk.Box(spacing=10); box.append(Gtk.Image.new_from_icon_name(icon)); box.append(Gtk.Label(label=title, xalign=0))
            row.set_child(box); sidebar.append(row)
        title_lbl = Gtk.Label(label="DASHBOARD"); title_lbl.add_css_class("sigil-page-title")

        def on_row(_lb, row):
            if row and row.page in holders:
                if win.get_visible():
                    snd("click")
                fresh = ensure(row.page)
                stack.set_visible_child_name(row.page); title_lbl.set_label(row.page.upper())
                page = pages[row.page]
                if not fresh and win.get_visible() and hasattr(page, "refresh"):
                    page.refresh()
        sidebar.connect("row-selected", on_row)
        brand = Gtk.Label(label="SIGIL // SETTINGS", xalign=0); brand.add_css_class("sigil-brand")
        brand.set_margin_top(16); brand.set_margin_bottom(8); brand.set_margin_start(20)
        side = Gtk.Box(orientation=Gtk.Orientation.VERTICAL); side.add_css_class("sigil-sidebar"); side.append(brand); side.append(sidebar)

        header = Adw.HeaderBar(); header.set_title_widget(title_lbl)
        view = Adw.ToolbarView(); view.add_top_bar(header); view.set_content(stack)
        if os.environ.get("SIGIL_NOSPLIT"):
            split = Gtk.Box(); split.append(side); split.append(view); view.set_hexpand(True)
        else:
            split = Adw.OverlaySplitView(sidebar=side, content=view, sidebar_width_fraction=0.22, min_sidebar_width=180, max_sidebar_width=220)
        toasts.set_child(split); win.set_content(toasts)

        first = next(i for i, p in enumerate(PAGES) if p[0] in holders)
        sidebar.select_row(sidebar.get_row_at_index(first))

        ctl = Gtk.ShortcutController()
        ctl.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("Escape"), Gtk.CallbackAction.new(lambda *_: (win.close(), True)[1])))
        win.add_controller(ctl)
        win.connect("close-request", lambda *_: (self.hide_win(), True)[1])  # close = hide, the app stays resident
        if os.environ.get("SIGIL_TIMING"):
            print(f"build {time.time() - T_START:.2f}s", file=sys.stderr)
            win.connect("map", lambda *_: print(f"map {time.time() - T_START:.2f}s", file=sys.stderr))
        return win


if __name__ == "__main__":
    App().run(sys.argv)
