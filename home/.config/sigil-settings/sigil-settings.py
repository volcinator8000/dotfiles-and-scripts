#!/usr/bin/env python3
"""SIGIL // SETTINGS — a small control panel for this Hyprland rice.

Pages: Sounds (typewriter key sounds, packs), Power (profile, brightness,
idle timers), Desktop (wallpaper, updates, service restarts).
Everything goes through the same scripts the bar and control center use.
"""
import os, re, subprocess, json
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio, Gdk

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
UPDATE_NOW = os.path.join(CFG, "waybar", "scripts", "update-now.sh")
RUNTIME = os.environ.get("XDG_RUNTIME_DIR", "/tmp")

CSS = """
.sigil-brand { font-family: "JetBrainsMono Nerd Font", monospace; font-size: 0.85em;
               letter-spacing: 0.18em; color: @accent_color;
               text-shadow: 0 0 10px alpha(@accent_color, 0.55); }
.sigil-mono { font-family: "JetBrainsMono Nerd Font", monospace; }
.sigil-dim { color: alpha(@window_fg_color, 0.55); }
preferencesgroup label.title, preferencesgroup .heading { font-family: "JetBrainsMono Nerd Font", monospace;
               letter-spacing: 0.1em; text-transform: uppercase; font-size: 0.8em;
               color: @accent_color; }
.boxed-list { border: 1px solid @borders; }
scale trough { min-height: 4px; }
scale highlight { background: @accent_color; box-shadow: 0 0 6px alpha(@accent_color, 0.6); }
scale slider { border-radius: 0; background: @accent_color; }
switch:checked { background: @accent_color; }
"""


# ── shell helpers ─────────────────────────────────────────────────────────────
def run(cmd, timeout=5):
    """Run a command (list or shell string) and return stdout, '' on failure."""
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True,
                           text=True, timeout=timeout)
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


# ── small widget helpers ──────────────────────────────────────────────────────
def scale_row(title, subtitle, value, on_change, lo=0, hi=100, step=1, fmt="{:.0f}%"):
    row = Adw.ActionRow(title=title, subtitle=subtitle)
    scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, step)
    scale.set_value(value)
    scale.set_size_request(240, -1)
    scale.set_valign(Gtk.Align.CENTER)
    label = Gtk.Label(label=fmt.format(value), width_chars=5, xalign=1)
    label.add_css_class("sigil-mono")
    pending = {"id": 0}

    def changed(s):
        v = s.get_value()
        label.set_label(fmt.format(v))
        if pending["id"]:
            GLib.source_remove(pending["id"])
        pending["id"] = GLib.timeout_add(150, lambda: (on_change(v), pending.update(id=0), False)[2])
    scale.connect("value-changed", changed)
    row.add_suffix(scale)
    row.add_suffix(label)
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


# ── pages ─────────────────────────────────────────────────────────────────────
class SoundsPage(Adw.PreferencesPage):
    def __init__(self, toast):
        super().__init__(title="Sounds", icon_name="audio-input-microphone-symbolic")
        self.toast = toast
        cfg = self.read_cfg()

        g = Adw.PreferencesGroup(title="Typewriter key sounds",
                                 description="Mechanical key clicks synthesised in the theme. "
                                             "Runs as a small daemon reading the keyboard.")
        self.enabled = Adw.SwitchRow(title="Key sounds", subtitle="Start or stop the daemon")
        self.enabled.set_active(run([KS_SH, "state"]) == "true")
        self.enabled.connect("notify::active", self.on_enabled)
        g.add(self.enabled)
        g.add(scale_row("Volume", "Master level of the mixer", float(cfg.get("volume", 0.45)) * 100,
                        lambda v: run([KS_SH, "volume", f"{v / 100:.2f}"])))
        self.add(g)

        g = Adw.PreferencesGroup(title="Sound pack",
                                 description="Packs live in ~/.config/keysound/packs/NAME/ as ten "
                                             "WAV files: key0-3, space, backspace, mod, enter, hold, release.")
        self.packs = sorted(d for d in os.listdir(os.path.join(KS, "packs"))
                            if os.path.isdir(os.path.join(KS, "packs", d)))
        self.pack = Adw.ComboRow(title="Active pack", subtitle="Switches live, no restart needed")
        self.pack.set_model(Gtk.StringList.new([self.pretty(p) for p in self.packs]))
        cur = cfg.get("pack", "cybersigil")
        self.pack.set_selected(self.packs.index(cur) if cur in self.packs else 0)
        self.pack.connect("notify::selected", self.on_pack)
        g.add(self.pack)
        g.add(button_row("Preview", "Plays the selected pack through the mixer",
                         ("Preview", self.preview, "suggested-action"),
                         ("Open folder", lambda: spawn(["xdg-open", os.path.join(KS, "packs")]), None)))
        g.add(button_row("Regenerate packs", "Re-synthesise the built-in packs from gen-sounds.py",
                         ("Regenerate", self.regen, None)))
        self.add(g)

    @staticmethod
    def pretty(name):
        return {"cybersigil": "Cybersigil (typewriter)", "animalese": "Animalese (Animal Crossing)"}.get(
            name, name.replace("-", " ").title())

    @staticmethod
    def read_cfg():
        out = {}
        try:
            for line in open(os.path.join(KS, "config")):
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
        except OSError:
            pass
        return out

    def on_enabled(self, row, _):
        run([KS_SH, "start" if row.get_active() else "stop"])
        self.toast(f"Key sounds {'started' if row.get_active() else 'stopped'}")

    def on_pack(self, row, _):
        name = self.packs[row.get_selected()]
        run([KS_SH, "pack", name])
        self.toast(f"Pack: {self.pretty(name)}")

    def preview(self):
        name = self.packs[self.pack.get_selected()]
        spawn(["python3", os.path.join(KS, "keysoundd.py"), "--demo", "--pack", name])

    def regen(self):
        for p in ("cybersigil", "animalese"):
            run(["python3", os.path.join(KS, "gen-sounds.py"), "--pack", p], timeout=120)
        run([KS_SH, "pack", self.packs[self.pack.get_selected()]])  # HUP reloads samples
        self.toast("Packs regenerated")


class PowerPage(Adw.PreferencesPage):
    def __init__(self, toast):
        super().__init__(title="Power", icon_name="battery-symbolic")
        self.toast = toast

        g = Adw.PreferencesGroup(title="Power profile")
        self.profiles = [l.strip().lstrip("* ").rstrip(":") for l in run(["powerprofilesctl", "list"]).splitlines()
                         if l.strip().endswith(":") and not l.startswith("    ")]
        self.profile = Adw.ComboRow(title="Profile", subtitle="power-profiles-daemon / amd-pstate-epp")
        self.profile.set_model(Gtk.StringList.new(self.profiles or ["unavailable"]))
        cur = run(["powerprofilesctl", "get"])
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
        g.add(scale_row("Brightness", "Panel backlight", cur_b,
                        lambda v: run(["brightnessctl", "-q", "set", f"{int(v)}%"]), lo=1))
        self.add(g)

        g = Adw.PreferencesGroup(title="Night light",
                                 description="hyprsunset warms the screen on a schedule; the override switch lasts "
                                             "until the next scheduled change.")
        ns = self.read_sunset()
        self.sched = Adw.SwitchRow(title="Schedule", subtitle="Run hyprsunset at login and follow the times below")
        self.sched.set_active(ns["enabled"])
        g.add(self.sched)
        self.night = Adw.SwitchRow(title="Night light now", subtitle="Manual override")
        self.night.set_active(run([NIGHTLIGHT, "state"]) == "true")
        self.night.connect("notify::active", lambda r, _: (run([NIGHTLIGHT, "on" if r.get_active() else "off"]),
                                                            self.toast("Night light " + ("on" if r.get_active() else "off"))))
        g.add(self.night)
        self.temp_val, self.gamma_val, self.day_val = ns["temp"], ns["gamma"], ns["day"]
        g.add(scale_row("Night warmth", "Colour temperature at night (lower = warmer); previews live", ns["temp"],
                        self.preview_temp, lo=2500, hi=6000, step=100, fmt="{:.0f} K"))
        g.add(scale_row("Night brightness", "Gamma applied with the warm tint; previews live", ns["gamma"],
                        self.preview_gamma, lo=40, hi=100, step=5))
        g.add(scale_row("Day warmth", "Daytime colour temperature; 6500 K = untouched", ns["day"],
                        self.preview_day, lo=4000, hi=6500, step=100, fmt="{:.0f} K"))
        self.start = Adw.EntryRow(title="Evening start (HH:MM)"); self.start.set_text(ns["start"])
        self.end = Adw.EntryRow(title="Morning end (HH:MM)"); self.end.set_text(ns["end"])
        g.add(self.start); g.add(self.end)
        g.add(button_row("Apply schedule", "Write hyprsunset.conf and restart hyprsunset",
                         ("Apply", self.apply_sunset, "suggested-action")))
        self.add(g)

        g = Adw.PreferencesGroup(title="Idle timers",
                                 description="Rewrites hypridle.conf and restarts hypridle. 0 disables a step.")
        t = self.read_idle()
        self.dim = self.spin("Dim after", "minutes", t["dim"] / 60, 0, 120, 0.5, 1)
        self.dim_level = self.spin("Dim level", "percent of full brightness", t["dim_level"], 1, 100, 5, 0)
        self.lock = self.spin("Lock after", "minutes", t["lock"] / 60, 0, 240, 0.5, 1)
        self.off = self.spin("Screen off after", "minutes", t["off"] / 60, 0, 240, 0.5, 1)
        self.sleep = self.spin("Sleep after", "minutes, suspend-then-hibernate", t["sleep"] / 60, 0, 480, 0.5, 1)
        for r in (self.dim, self.dim_level, self.lock, self.off, self.sleep):
            g.add(r)
        g.add(button_row("Apply", "Write the config and restart the idle daemon",
                         ("Apply", self.apply_idle, "suggested-action")))
        self.add(g)

    @staticmethod
    def read_sunset():
        d = {"start": "21:00", "end": "07:30", "temp": 4200, "gamma": 100, "day": 6500, "enabled": True}
        try:
            text = open(HYPRSUNSET).read()
        except OSError:
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
                g = re.search(r"gamma\s*=\s*(\d+)", b)
                d["gamma"] = int(g.group(1)) if g else 100
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
            run(["hyprctl", "hyprsunset", "identity"] if self.day_val >= 6500 else
                ["hyprctl", "hyprsunset", "temperature", str(self.day_val)])

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
                    f"# schedule = {'on' if enabled else 'off'}\n"
                    "max-gamma = 150\n\n"
                    f"profile {{\n    time = {times[1]}\n{day}}}\n\n"
                    f"profile {{\n    time = {times[0]}\n    temperature = {self.temp_val}\n{night_gamma}}}\n")
        run([NIGHTLIGHT, "reset"])
        if enabled:
            restart("hyprsunset")
        else:
            run(["hyprctl", "hyprsunset", "identity"]); run(["hyprctl", "hyprsunset", "gamma", "100"])
            run(["pkill", "-x", "hyprsunset"])
        GLib.timeout_add(900, lambda: (self.night.set_active(run([NIGHTLIGHT, "state"]) == "true"), False)[1])
        self.toast("Night light schedule applied" if enabled else "Night light schedule disabled")

    @staticmethod
    def spin(title, subtitle, value, lo, hi, step, digits):
        r = Adw.SpinRow.new_with_range(lo, hi, step)
        r.set_title(title); r.set_subtitle(subtitle); r.set_digits(digits); r.set_value(value)
        return r

    def on_profile(self, row, _):
        if self.profiles:
            p = self.profiles[row.get_selected()]
            run(["powerprofilesctl", "set", p])
            self.toast(f"Profile: {p}")

    @staticmethod
    def read_idle():
        t = {"dim": 120, "dim_level": 15, "lock": 300, "off": 600, "sleep": 630}
        try:
            text = open(HYPRIDLE).read()
        except OSError:
            return t
        for block in re.findall(r"listener\s*\{(.*?)\}", text, re.S):
            m = re.search(r"timeout\s*=\s*(\d+)", block)
            cmd = re.search(r"on-timeout\s*=\s*(.*)", block)
            if not (m and cmd):
                continue
            secs, c = int(m.group(1)), cmd.group(1)
            if "brightnessctl" in c:
                t["dim"] = secs
                lvl = re.search(r"set\s+(\d+)%", c)
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
        parts = ["general {",
                 "    # plain hyprlock: a stale/hung hyprlock must not block re-locking",
                 "    lock_cmd = hyprlock",
                 "    before_sleep_cmd = loginctl lock-session",
                 "    after_sleep_cmd = hyprctl dispatch 'hl.dsp.dpms(\"on\")'",
                 "    inhibit_sleep = 3   # delay suspend until the lock screen is drawn",
                 "}", "",
                 "# generated by sigil-settings; edit there or by hand (timeouts in seconds)"]
        if dim:
            parts += ["", "listener {", f"    timeout = {dim}", f"    on-timeout = brightnessctl -s set {level}%",
                      "    on-resume = brightnessctl -r", "}"]
        if lock:
            parts += ["", "listener {", f"    timeout = {lock}", "    on-timeout = loginctl lock-session", "}"]
        if off:
            parts += ["", "listener {", f"    timeout = {off}", "    on-timeout = hyprctl dispatch 'hl.dsp.dpms(\"off\")'",
                      "    on-resume = hyprctl dispatch 'hl.dsp.dpms(\"on\")'", "}"]
        if sleep:
            parts += ["", "listener {", f"    timeout = {sleep}", "    on-timeout = systemctl suspend-then-hibernate", "}"]
        with open(HYPRIDLE, "w") as f:
            f.write("\n".join(parts) + "\n")
        restart("hypridle")
        self.toast("hypridle restarted with new timers")


class DesktopPage(Adw.PreferencesPage):
    def __init__(self, toast):
        super().__init__(title="Desktop", icon_name="preferences-desktop-wallpaper-symbolic")
        self.toast = toast

        g = Adw.PreferencesGroup(title="Wallpaper")
        self.wall = self.read_wallpaper()
        self.wall_row = button_row("Image", self.wall or "none set", ("Choose…", self.pick_wallpaper, None))
        g.add(self.wall_row)
        self.add(g)

        g = Adw.PreferencesGroup(title="Updates")
        self.upd = button_row("Pending packages", self.update_text(),
                              ("Check now", self.check_updates, None),
                              ("Update", lambda: spawn([UPDATE_NOW]), "suggested-action"))
        g.add(self.upd)
        self.add(g)

        g = Adw.PreferencesGroup(title="Services", description="Restart a piece of the desktop without logging out.")
        for title, sub, cb in (
            ("Waybar", "status bar", lambda: restart("waybar")),
            ("SwayNC", "notifications + control center (reloads config and style)",
             lambda: (run(["swaync-client", "-R"]), run(["swaync-client", "-rs"]))),
            ("hypridle", "idle daemon", lambda: restart("hypridle")),
            ("hyprpaper", "wallpaper daemon", lambda: restart("hyprpaper")),
            ("Key sounds", "typewriter daemon", lambda: run([KS_SH, "restart"])),
            ("Hyprland config", "hyprctl reload", lambda: run(["hyprctl", "reload"])),
        ):
            g.add(button_row(title, sub, ("Restart", lambda cb=cb, t=title: (cb(), self.toast(f"{t} restarted")), None)))
        self.add(g)

    @staticmethod
    def read_wallpaper():
        try:
            m = re.search(r"^\s*path\s*=\s*(.+)$", open(HYPRPAPER).read(), re.M)
            return m.group(1).strip() if m else ""
        except OSError:
            return ""

    def pick_wallpaper(self):
        dlg = Gtk.FileDialog(title="Choose wallpaper")
        f = Gtk.FileFilter(); f.set_name("Images"); f.add_mime_type("image/*")
        fl = Gio.ListStore.new(Gtk.FileFilter); fl.append(f)
        dlg.set_filters(fl)
        start = os.path.join(HOME, "Pictures", "Wallpapers")
        if os.path.isdir(start):
            dlg.set_initial_folder(Gio.File.new_for_path(start))
        dlg.open(self.get_root(), None, self.on_wallpaper)

    def on_wallpaper(self, dlg, res):
        try:
            gfile = dlg.open_finish(res)
        except GLib.Error:
            return
        path = gfile.get_path()
        with open(HYPRPAPER, "w") as f:
            f.write("wallpaper {\n    monitor =\n    path = %s\n    fit_mode = cover\n}\nsplash = false\n" % path)
        # keep hyprlock's blurred background in sync when it pointed at the old wallpaper
        try:
            text = open(HYPRLOCK).read()
            if self.wall and self.wall in text:
                open(HYPRLOCK, "w").write(text.replace(self.wall, path))
        except OSError:
            pass
        self.wall = path
        self.wall_row.set_subtitle(path)
        restart("hyprpaper")
        self.toast("Wallpaper applied")

    @staticmethod
    def update_text():
        try:
            d = json.load(open(os.path.join(RUNTIME, "waybar-updates.json")))
            n = d.get("text", "").strip()
            return f"{n or 0} pending" if n and n != "" else "up to date"
        except (OSError, ValueError):
            return "not checked yet"

    def check_updates(self):
        run(["pkill", "-RTMIN+9", "-x", "waybar"])
        self.toast("Checking for updates…")
        GLib.timeout_add(8000, lambda: (self.upd.set_subtitle(self.update_text()), False)[1])


# ── application ───────────────────────────────────────────────────────────────
class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.sigil.Settings", flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = self.build()
        win.present()

    def build(self):
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        prov = Gtk.CssProvider(); prov.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        win = Adw.ApplicationWindow(application=self, title="SIGIL // SETTINGS", default_width=800, default_height=620)
        toasts = Adw.ToastOverlay()
        toast = lambda msg: toasts.add_toast(Adw.Toast(title=msg, timeout=2))

        stack = Adw.ViewStack()
        for page in (SoundsPage(toast), PowerPage(toast), DesktopPage(toast)):
            stack.add_titled_with_icon(page, page.get_title().lower(), page.get_title(), page.get_icon_name())
        import sys
        if "--page" in sys.argv:  # sigil-settings.py --page power
            stack.set_visible_child_name(sys.argv[sys.argv.index("--page") + 1])

        header = Adw.HeaderBar()
        brand = Gtk.Label(label="SIGIL // SETTINGS"); brand.add_css_class("sigil-brand")
        header.pack_start(brand)
        switcher = Adw.ViewSwitcher(stack=stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        header.set_title_widget(switcher)

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(stack)
        toasts.set_child(view)
        win.set_content(toasts)

        # Esc closes
        ctl = Gtk.ShortcutController()
        ctl.add_shortcut(Gtk.Shortcut.new(Gtk.ShortcutTrigger.parse_string("Escape"),
                                          Gtk.CallbackAction.new(lambda *_: (win.close(), True)[1])))
        win.add_controller(ctl)
        return win


if __name__ == "__main__":
    App().run(None)
