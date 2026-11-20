"""Original light 'science explainer' background music (own work, synthesised).

Curious, gentle mood: marimba-like arpeggio, plucked bass, soft pad, very light
shaker, occasional glockenspiel; Dm7 - Bbmaj7 - Fmaj7 - C(add9) at 100 bpm.
Usage: python3 make_bgm2.py out.wav seconds [duck_until_seconds]
The music is quieter (ducked) until `duck_until` so it sits under narration,
then rises for the closing animation.
"""
import sys
import wave

import numpy as np

SR = 48000
OUT, DUR = sys.argv[1], float(sys.argv[2])
DUCK = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(3)
BPM = 100
beat = 60 / BPM
bar = 4 * beat


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


chords = [[50, 53, 57, 60], [46, 50, 53, 57], [41, 45, 48, 52], [48, 52, 55, 62]]  # Dm7 Bbmaj7 Fmaj7 Cadd9
roots = [38, 34, 41, 36]
L = np.zeros(n)
Rr = np.zeros(n)


def add(sig, start, pan=0.0, gain=1.0):
    i0 = int(start * SR)
    if i0 >= n:
        return
    m = min(len(sig), n - i0)
    L[i0:i0 + m] += sig[:m] * gain * (1 - pan) / 2 * 2 ** 0.5
    Rr[i0:i0 + m] += sig[:m] * gain * (1 + pan) / 2 * 2 ** 0.5


def note(f, length, kind):
    tt = np.arange(int(length * SR)) / SR
    if kind == "marimba":
        return np.exp(-tt * 7) * (np.sin(2 * np.pi * f * tt) + 0.35 * np.exp(-tt * 20) * np.sin(2 * np.pi * 4 * f * tt))
    if kind == "bass":
        return np.exp(-tt * 4.5) * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 3 * f * tt) / 3)
    if kind == "glock":
        return np.exp(-tt * 3) * (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2.76 * f * tt))
    if kind == "shaker":
        x = rng.standard_normal(len(tt)) * np.exp(-tt * 90)
        return np.diff(np.concatenate([[0], x]))  # crude high-pass
    raise ValueError(kind)


pattern = [0, 2, 1, 3, 2, 1, 3, 2]  # arpeggio order over 8 eighth notes
nbars = int(np.ceil(DUR / bar))
for b in range(nbars):
    ch = chords[b % 4]
    t0 = b * bar
    for k in range(8):
        f = hz(ch[pattern[k]] + 12)
        add(note(f, 1.0, "marimba"), t0 + k * beat / 2, pan=0.25 if k % 2 else -0.25, gain=0.55 if k % 2 else 0.75)
    for k in (0, 2):
        add(note(hz(roots[b % 4] + (0 if k == 0 else 7)), 1.2, "bass"), t0 + k * beat, gain=0.8)
    for k in range(8):
        if k % 2:
            add(note(0, 0.08, "shaker"), t0 + k * beat / 2, pan=0.4, gain=0.10)
    if b % 2 == 0:
        add(note(hz(ch[-1] + 24), 2.0, "glock"), t0 + 3.5 * beat, pan=-0.3, gain=0.22)
    # pad
    seg = int(bar * SR) + int(0.8 * SR)
    tt = np.arange(seg) / SR
    env = np.minimum(1, tt / 0.6) * np.clip((bar + 0.8 - tt) / 0.8, 0, 1)
    pad = sum(np.sin(2 * np.pi * hz(m) * tt * 2 ** (d / 1200)) for m in ch for d in (-6, 6)) / (2 * len(ch))
    add(pad * env, t0, gain=0.22)

ir_len = int(1.4 * SR)
ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / SR * 4.0)
ir[0] = 1.0
F = 1 << int(np.ceil(np.log2(n + ir_len)))


def verb(x, roll):
    y = np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(np.roll(ir, roll), F), F)[:n]
    return y / (np.max(np.abs(y)) + 1e-9) * np.max(np.abs(x))


outL = 0.72 * L + 0.28 * verb(L, 0)
outR = 0.72 * Rr + 0.28 * verb(Rr, 29)
fade = np.minimum(1, t / 1.0) * np.clip((DUR - t) / 2.0, 0, 1)
if DUCK > 0:
    duck = np.where(t < DUCK, 0.28, 1.0)
    k = int(1.2 * SR)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")  # smooth 1.2 s ramp
    fade = fade * duck
st = np.stack([outL * fade, outR * fade], 1)
st /= np.max(np.abs(st)) + 1e-9
st *= 0.85
w = wave.open(OUT, "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st * 32767).astype(np.int16).tobytes())
w.close()
print("wrote", OUT, DUR, "s, ducked until", DUCK)
