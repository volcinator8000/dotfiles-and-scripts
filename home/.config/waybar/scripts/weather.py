#!/usr/bin/env python3
"""custom/weather: local weather from wttr.in (location by IP, no key). Caches 15 min in the runtime dir;
shows the last good reading when offline. Click = refresh (signal 11)."""
import json, os, sys, time, urllib.request
RT = os.environ.get("XDG_RUNTIME_DIR", "/tmp"); CACHE = os.path.join(RT, "waybar-weather.json"); TTL = 900
ICON = {113: ("󰖙", "󰖔"), 116: ("󰖕", "󰼱"), 119: ("󰖐", "󰖐"), 122: ("󰖐", "󰖐"), 143: ("󰖑", "󰖑"), 248: ("󰖑", "󰖑"), 260: ("󰖑", "󰖑"),
        176: ("󰖗", "󰖗"), 263: ("󰖗", "󰖗"), 266: ("󰖗", "󰖗"), 293: ("󰖗", "󰖗"), 296: ("󰖗", "󰖗"), 353: ("󰖗", "󰖗"),
        299: ("󰖖", "󰖖"), 302: ("󰖖", "󰖖"), 305: ("󰖖", "󰖖"), 308: ("󰖖", "󰖖"), 356: ("󰖖", "󰖖"), 359: ("󰖖", "󰖖"),
        179: ("󰙿", "󰙿"), 182: ("󰙿", "󰙿"), 185: ("󰙿", "󰙿"), 311: ("󰙿", "󰙿"), 314: ("󰙿", "󰙿"), 317: ("󰙿", "󰙿"), 320: ("󰙿", "󰙿"),
        350: ("󰙿", "󰙿"), 362: ("󰙿", "󰙿"), 365: ("󰙿", "󰙿"), 374: ("󰙿", "󰙿"), 377: ("󰙿", "󰙿"),
        227: ("󰖘", "󰖘"), 230: ("󰖘", "󰖘"), 323: ("󰖘", "󰖘"), 326: ("󰖘", "󰖘"), 329: ("󰖘", "󰖘"), 332: ("󰖘", "󰖘"), 335: ("󰖘", "󰖘"),
        338: ("󰖘", "󰖘"), 368: ("󰖘", "󰖘"), 371: ("󰖘", "󰖘"), 395: ("󰖘", "󰖘"),
        200: ("󰖓", "󰖓"), 386: ("󰖓", "󰖓"), 389: ("󰖓", "󰖓"), 392: ("󰖓", "󰖓")}

def fetch():
    req = urllib.request.Request("https://wttr.in/?format=j1", headers={"User-Agent": "curl/8"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)

def hm(s):  # "06:58 AM" -> "06:58"
    try:
        return time.strftime("%H:%M", time.strptime(s.strip(), "%I:%M %p"))
    except ValueError:
        return s

def render(d, stale):
    c = d["current_condition"][0]; a = d["nearest_area"][0]; ast = d["weather"][0]["astronomy"][0]
    code = int(c["weatherCode"]); now = time.strftime("%H:%M")
    day = hm(ast["sunrise"]) <= now < hm(ast["sunset"])
    icon = ICON.get(code, ("󰖐", "󰖐"))[0 if day else 1]
    desc = c["weatherDesc"][0]["value"]
    text = f"{icon} {c['temp_C']}°"
    lines = [f"{a['areaName'][0]['value']}, {a['country'][0]['value']}" + ("  (offline, last reading)" if stale else ""),
             f"{desc} · feels like {c['FeelsLikeC']}°",
             f"humidity {c['humidity']}% · wind {c['windspeedKmph']} km/h {c['winddir16Point']} · {c['precipMM']} mm",
             f"sunrise {hm(ast['sunrise'])} · sunset {hm(ast['sunset'])}", ""]
    for w in d["weather"][:3]:
        dn = time.strftime("%a", time.strptime(w["date"], "%Y-%m-%d")); mid = w["hourly"][4]  # 12:00
        lines.append(f"{dn}  {w['mintempC']}° / {w['maxtempC']}°  {mid['weatherDesc'][0]['value']}  ☂ {mid['chanceofrain']}%")
    cls = "night" if not day else ("rain" if code >= 176 and code not in (200, 386, 389, 392) else "clear")
    return {"text": text, "tooltip": "\n".join(lines), "class": cls + (" stale" if stale else ""), "alt": desc}

def main():
    force = "--refresh" in sys.argv
    cached = None
    try:
        cached = json.load(open(CACHE))
        if not force and time.time() - cached["at"] < TTL:
            print(json.dumps(render(cached["data"], False))); return
    except (OSError, ValueError, KeyError):
        pass
    try:
        data = fetch(); json.dump({"at": time.time(), "data": data}, open(CACHE, "w"))
        print(json.dumps(render(data, False)))
    except Exception:
        if cached:
            print(json.dumps(render(cached["data"], True)))
        else:
            print(json.dumps({"text": "󰖐 —", "tooltip": "weather: no data yet (offline?)", "class": "stale"}))

main()
