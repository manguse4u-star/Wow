"""Original ambient background music for the closing animation (own work, no samples).

Soft pad chords (Cmaj9 - Am9 - Fmaj9 - G6sus) + a gentle plucked arpeggio,
with a synthetic reverb.  Writes a 48 kHz stereo WAV of the requested length.
Usage: python3 make_bgm.py out.wav seconds
"""
import sys
import wave

import numpy as np

SR = 48000
OUT, DUR = sys.argv[1], float(sys.argv[2])
n = int(SR * DUR)
t = np.arange(n) / SR
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


chords = [[48, 55, 59, 62, 64], [45, 52, 55, 59, 60], [41, 48, 52, 55, 57], [43, 50, 55, 57, 62]]
bar = DUR / len(chords)

pad = np.zeros(n)
for i, ch in enumerate(chords):
    s, e = i * bar, min(DUR, (i + 1) * bar + 1.2)
    m = (t >= s) & (t < e)
    tt = t[m] - s
    env = np.minimum(1, tt / 1.0) * np.clip((e - s - tt) / 1.2, 0, 1)
    for note in ch:
        f = hz(note)
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            pad[m] += env * (np.sin(2 * np.pi * ff * tt) + 0.25 * np.sin(4 * np.pi * ff * tt)) / len(ch)

pluck = np.zeros(n)
step = 60 / 84 / 2  # eighth notes at 84 bpm
k = 0
while k * step < DUR - 0.5:
    st = k * step
    ch = chords[min(int(st // bar), len(chords) - 1)]
    note = ch[[1, 2, 3, 4, 3, 2][k % 6]] + 12
    i0 = int(st * SR)
    L = min(n - i0, int(1.6 * SR))
    tt = np.arange(L) / SR
    f = hz(note)
    pluck[i0:i0 + L] += np.exp(-tt * 3.5) * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(6 * np.pi * f * tt)) * (0.9 if k % 2 == 0 else 0.6)
    k += 1

dry = 0.55 * pad + 0.35 * pluck
ir_len = int(1.8 * SR)
ir = rng.standard_normal(ir_len) * np.exp(-np.arange(ir_len) / SR * 3.2)
ir[0] = 1.0
L = len(dry) + ir_len
F = 1 << int(np.ceil(np.log2(L)))
wetL = np.fft.irfft(np.fft.rfft(dry, F) * np.fft.rfft(ir, F), F)[:n]
ir2 = np.roll(ir, 37)
wetR = np.fft.irfft(np.fft.rfft(dry, F) * np.fft.rfft(ir2, F), F)[:n]
wetL /= np.max(np.abs(wetL)) + 1e-9
wetR /= np.max(np.abs(wetR)) + 1e-9
dn = dry / (np.max(np.abs(dry)) + 1e-9)
left, right = 0.6 * dn + 0.4 * wetL, 0.6 * dn + 0.4 * wetR
fade = np.minimum(1, t / 0.8) * np.clip((DUR - t) / 1.8, 0, 1)
st = np.stack([left * fade, right * fade], 1)
st /= np.max(np.abs(st)) + 1e-9
st *= 0.8
w = wave.open(OUT, "wb")
w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st * 32767).astype(np.int16).tobytes())
w.close()
print("wrote", OUT, DUR, "s")
