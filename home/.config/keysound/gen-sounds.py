#!/usr/bin/env python3
"""Synthesise the cybersigilism typing sound set (pure python, 44.1 kHz mono 16-bit)."""
import math, random, struct, wave, os, sys
SR = 44100
PACK = sys.argv[sys.argv.index("--pack") + 1] if "--pack" in sys.argv else "cybersigil"
OUT = os.path.expanduser(f"~/.config/keysound/packs/{PACK}")
os.makedirs(OUT, exist_ok=True)
random.seed(3)

def env_exp(n, tau):  # exponential decay
    return [math.exp(-i / (tau * SR)) for i in range(n)]

def noise(n): return [random.uniform(-1, 1) for _ in range(n)]

def lowpass(x, cutoff):
    rc = 1 / (2 * math.pi * cutoff); dt = 1 / SR; a = dt / (rc + dt)
    y = [0.0] * len(x); prev = 0.0
    for i, v in enumerate(x): prev = prev + a * (v - prev); y[i] = prev
    return y

def highpass(x, cutoff):
    return [v - w for v, w in zip(x, lowpass(x, cutoff))]

def sine(n, f, f_end=None, phase=0.0):
    out = []; ph = phase
    for i in range(n):
        fi = f if f_end is None else f + (f_end - f) * i / n
        ph += 2 * math.pi * fi / SR; out.append(math.sin(ph))
    return out

def bitcrush(x, bits=6):
    q = 2 ** (bits - 1)
    return [round(v * q) / q for v in x]

def mix(*parts):
    n = max(len(p) for p in parts); out = [0.0] * n
    for p in parts:
        for i, v in enumerate(p): out[i] += v
    return out

def scale(x, g): return [v * g for v in x]
def mul(x, e): return [v * w for v, w in zip(x, e)]

def fade_out(x, ms):
    n = int(SR * ms / 1000); L = len(x)
    return [v * (min(1.0, (L - i) / n) if i > L - n else 1.0) for i, v in enumerate(x)]

def write(name, x, gain=0.9):
    x = fade_out(x, 8)
    peak = max(1e-9, max(abs(v) for v in x)); x = [v / peak * gain for v in x]
    with wave.open(os.path.join(OUT, name), "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in x))

def clack(len_ms=38, tone=2600, tone_gain=0.35, body=140, body_gain=0.5, crush=0):
    """typewriter-ish clack: filtered noise transient + hi tick + low thump"""
    n = int(SR * len_ms / 1000)
    nz = mul(highpass(lowpass(noise(n), 3200), 500), env_exp(n, 0.0035))
    tick = mul(sine(n, tone * 0.8, tone * 0.65), env_exp(n, 0.0025))
    thump = mul(sine(n, body, body * 0.6), env_exp(n, 0.010))
    x = mix(nz, scale(tick, tone_gain), scale(thump, body_gain))
    return bitcrush(x, crush) if crush else x


def animalese():
    """Animal Crossing style 'Animalese': short vowel-like blips, random pitch on a small scale."""
    def vowel(n, f0, formants, gain=1.0):
        # harmonic stack shaped by two formant peaks -> vowel-ish timbre
        out = [0.0] * n
        for h in range(1, 14):
            fh = f0 * h
            amp = sum(math.exp(-((fh - fc) / bw) ** 2) for fc, bw in formants) / h ** 0.6
            sig = sine(n, fh, fh * 0.97)
            for i in range(n): out[i] += sig[i] * amp
        return scale(out, gain)
    def blip(len_ms, f0, formants, attack_ms=4, decay=0.03):
        n = int(SR * len_ms / 1000)
        env = [min(1.0, i / (SR * attack_ms / 1000)) * math.exp(-max(0, i - SR * 0.012) / (decay * SR)) for i in range(n)]
        return fade_out(mul(vowel(n, f0, formants), env), 10)
    A  = [(700, 220), (1200, 300)]   # "a"
    E  = [(500, 200), (1900, 350)]   # "e"
    O  = [(450, 200), (900, 250)]    # "o"
    U  = [(350, 180), (800, 220)]    # "u"
    scale_hz = [392, 440, 494, 587, 659]        # G A B D E (pentatonic)
    for i, (f0, form) in enumerate(zip(scale_hz[:4], [A, E, O, A])):
        write(f"key{i}.wav", blip(75, f0 * 1.6, form), 0.5)
    write("space.wav", blip(90, 330 * 1.4, U, decay=0.04), 0.45)
    write("backspace.wav", blip(70, 494 * 1.4, O, decay=0.025), 0.4)
    write("mod.wav", blip(55, 659 * 1.4, E, decay=0.02), 0.32)
    # enter: two-note chirp up (D -> G)
    n1 = blip(80, 587 * 1.4, A); n2 = blip(140, 784 * 1.4, E, decay=0.05)
    write("enter.wav", n1 + [0.0] * int(SR * 0.02) + n2, 0.5)
    # hold: rising trill (three quick notes)
    trill = []
    for f in (440, 494, 587):
        trill += blip(60, f * 1.6, A, decay=0.02) + [0.0] * int(SR * 0.01)
    write("hold.wav", trill, 0.42)
    # release: single falling blip
    n = int(SR * 0.12)
    env = [min(1.0, i / (SR * 0.004)) * math.exp(-max(0, i - SR * 0.01) / (0.035 * SR)) for i in range(n)]
    write("release.wav", fade_out(mul(vowel(n, 520, O), env), 40), 0.3)

if PACK == "animalese":
    animalese()
else:
    # ── key variants (pitch variation is applied at playback by picking one of 4 files) ──
    for i in range(4):
        write(f"key{i}.wav", clack(tone=2400 + i * 180, tone_gain=0.22, body=130 + i * 12, body_gain=0.45), 0.55)
    write("space.wav", clack(len_ms=50, tone=1400, tone_gain=0.12, body=95, body_gain=0.8), 0.6)
    write("backspace.wav", mix(clack(len_ms=34, tone=1900, tone_gain=0.25, body=120, body_gain=0.35),
                               scale(mul(sine(int(SR*0.05), 900, 1500), env_exp(int(SR*0.05), 0.012)), 0.18)), 0.5)
    write("mod.wav", clack(len_ms=22, tone=3200, tone_gain=0.15, body=180, body_gain=0.22), 0.38)

    # enter: mechanical clack + carriage-return "ding" bell (inharmonic partials) + short shimmer sweep
    n = int(SR * 0.55)
    bell = mix(scale(mul(sine(n, 1318), env_exp(n, 0.12)), 1.0),
               scale(mul(sine(n, 1318 * 2.76), env_exp(n, 0.05)), 0.22),
               scale(mul(sine(n, 1318 * 0.5), env_exp(n, 0.18)), 0.3))
    shimmer = scale(mul(sine(int(SR*0.12), 3000, 6500), env_exp(int(SR*0.12), 0.03)), 0.15)
    write("enter.wav", mix(clack(len_ms=42, tone=1800, tone_gain=0.18, body=110, body_gain=0.6), scale(bell, 0.45)), 0.5)

    # hold start: digital spin-up sweep with bitcrush (the "charging" sound)
    n = int(SR * 0.28)
    sweep = mul(bitcrush(sine(n, 180, 720), 5), [min(1, i / (SR * 0.02)) * math.exp(-max(0, i - SR*0.2) / (SR*0.03)) for i in range(n)])
    buzz = mul(bitcrush(sine(n, 60, 110), 4), [0.5 * min(1, i / (SR*0.05)) for i in range(n)])
    write("hold.wav", mix(scale(lowpass(sweep, 2500), 0.7), scale(buzz, 0.45)), 0.5)

    # hold release: descending blip
    n = int(SR * 0.16)
    write("release.wav", fade_out(mul(lowpass(bitcrush(sine(n, 760, 320), 6), 2200), env_exp(n, 0.04)), 60), 0.26)

print(PACK, "->", sorted(os.listdir(OUT)))
