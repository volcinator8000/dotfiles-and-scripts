#!/usr/bin/env python3
"""custom/weather: local weather from open-meteo (location by IP, no API key).

Was wttr.in, which accepts the TCP connection and then never answers - the widget
sat on "no data" forever while the rest of the network was fine. open-meteo is a
plain JSON API with no key and no rate limit worth worrying about.

Caches the reading 15 min and the IP lookup 24 h in the runtime dir, and falls
back to the last good reading when offline. Click = refresh (signal 11).
"""
import json, os, sys, time, urllib.request

RT = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
CACHE = os.path.join(RT, "waybar-weather.json")
LOC_CACHE = os.path.join(RT, "waybar-weather-loc.json")
TTL, LOC_TTL = 900, 86400

# glyphs lifted verbatim from the wttr.in version of this script, by code point
SUN      = "\U000f0599"
MOON     = "\U000f0594"
PCLOUD_D = "\U000f0595"
PCLOUD_N = "\U000f0f31"
CLOUD    = "\U000f0590"
FOG      = "\U000f0591"
DRIZZLE  = "\U000f0597"   # light rain glyph
RAIN     = "\U000f0596"   # heavy rain glyph
SNOW     = "\U000f067f"
SLEET    = "\U000f0598"
STORM    = "\U000f0593"

# WMO weather interpretation codes -> (day icon, night icon, description)
WMO = {
    0:  (SUN, MOON, "clear sky"),
    1:  (SUN, MOON, "mainly clear"),
    2:  (PCLOUD_D, PCLOUD_N, "partly cloudy"),
    3:  (CLOUD, CLOUD, "overcast"),
    45: (FOG, FOG, "fog"),
    48: (FOG, FOG, "depositing rime fog"),
    51: (DRIZZLE, DRIZZLE, "light drizzle"),
    53: (DRIZZLE, DRIZZLE, "drizzle"),
    55: (RAIN, RAIN, "dense drizzle"),
    56: (SLEET, SLEET, "freezing drizzle"),
    57: (SLEET, SLEET, "dense freezing drizzle"),
    61: (DRIZZLE, DRIZZLE, "light rain"),
    63: (RAIN, RAIN, "rain"),
    65: (RAIN, RAIN, "heavy rain"),
    66: (SLEET, SLEET, "freezing rain"),
    67: (SLEET, SLEET, "heavy freezing rain"),
    71: (SNOW, SNOW, "light snow"),
    73: (SNOW, SNOW, "snow"),
    75: (SNOW, SNOW, "heavy snow"),
    77: (SNOW, SNOW, "snow grains"),
    80: (DRIZZLE, DRIZZLE, "light showers"),
    81: (RAIN, RAIN, "showers"),
    82: (RAIN, RAIN, "violent showers"),
    85: (SNOW, SNOW, "snow showers"),
    86: (SNOW, SNOW, "heavy snow showers"),
    95: (STORM, STORM, "thunderstorm"),
    96: (STORM, STORM, "thunderstorm with hail"),
    99: (STORM, STORM, "thunderstorm with heavy hail"),
}
COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
RAINY = set(range(51, 87))   # precipitation; thunder keeps its own class


def get(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "waybar-weather/2"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def location():
    """Coarse position from the public IP, cached a day (the API is rate limited)."""
    try:
        c = json.load(open(LOC_CACHE))
        if time.time() - c["at"] < LOC_TTL:
            return c["loc"]
    except (OSError, ValueError, KeyError):
        pass
    d = get("https://ipapi.co/json/")
    loc = {"lat": d["latitude"], "lon": d["longitude"],
           "city": d.get("city") or "?", "country": d.get("country_name") or ""}
    try:
        json.dump({"at": time.time(), "loc": loc}, open(LOC_CACHE, "w"))
    except OSError:
        pass
    return loc


def fetch():
    loc = location()
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={loc['lat']}&longitude={loc['lon']}"
           "&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
           "precipitation,weather_code,wind_speed_10m,wind_direction_10m"
           "&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,"
           "precipitation_probability_max"
           "&timezone=auto&forecast_days=3")
    d = get(url)
    d["_loc"] = loc
    return d


def render(d, stale):
    cur, day, loc = d["current"], d["daily"], d["_loc"]
    code = int(cur["weather_code"])
    now = time.strftime("%H:%M")
    sunrise, sunset = day["sunrise"][0][11:16], day["sunset"][0][11:16]
    is_day = sunrise <= now < sunset
    icon_d, icon_n, desc = WMO.get(code, (CLOUD, CLOUD, f"code {code}"))
    icon = icon_d if is_day else icon_n
    temp = round(cur["temperature_2m"])

    wind_dir = COMPASS[int((cur["wind_direction_10m"] + 11.25) % 360 // 22.5)]
    head = f"{loc['city']}, {loc['country']}" + ("  (offline, last reading)" if stale else "")
    lines = [head,
             f"{desc} · feels like {round(cur['apparent_temperature'])}°",
             f"humidity {cur['relative_humidity_2m']}% · "
             f"wind {round(cur['wind_speed_10m'])} km/h {wind_dir} · "
             f"{cur['precipitation']} mm",
             f"sunrise {sunrise} · sunset {sunset}", ""]
    for i in range(len(day["time"])):
        dn = time.strftime("%a", time.strptime(day["time"][i], "%Y-%m-%d"))
        dcode = int(day["weather_code"][i])
        ddesc = WMO.get(dcode, (None, None, f"code {dcode}"))[2]
        lines.append(f"{dn}  {round(day['temperature_2m_min'][i])}° / "
                     f"{round(day['temperature_2m_max'][i])}°  {ddesc}  "
                     f"☂ {day['precipitation_probability_max'][i]}%")

    cls = "night" if not is_day else ("rain" if code in RAINY else "clear")
    return {"text": f"{icon} {temp}°", "tooltip": "\n".join(lines),
            "class": cls + (" stale" if stale else ""), "alt": desc}


def main():
    force = "--refresh" in sys.argv
    cached = None
    try:
        cached = json.load(open(CACHE))
        if not force and time.time() - cached["at"] < TTL:
            print(json.dumps(render(cached["data"], False)))
            return
    except (OSError, ValueError, KeyError):
        pass
    try:
        data = fetch()
        try:
            json.dump({"at": time.time(), "data": data}, open(CACHE, "w"))
        except OSError:
            pass
        print(json.dumps(render(data, False)))
    except Exception:
        if cached:
            print(json.dumps(render(cached["data"], True)))
        else:
            print(json.dumps({"text": f"{CLOUD} —",
                              "tooltip": "weather: no data yet (offline?)", "class": "stale"}))


main()
