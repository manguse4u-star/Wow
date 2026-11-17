"""Simulated figure for the 'measuring spreading rate' slide.

Magnetic anomaly profile across a symmetric ridge with a half-spreading rate of
2 cm/yr (= 20 km/Myr).  Polarity intervals are the major chrons/subchrons of the
geomagnetic polarity time scale, GTS2012 (Ogg, 2012).  The anomaly is a
simplified forward model: a thin magnetised layer 3 km below the sensor,
vertical magnetisation and vertical field (i.e. a high-latitude ridge), so the
anomaly is symmetric.  Output: SVG (rasterised to PNG by svg2png.js).
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "deliverables", "assets_png")

# normal-polarity intervals (Ma), GTS2012 (Ogg, 2012); everything else reversed
NORMAL = [(0.0, 0.781), (0.988, 1.072), (1.778, 1.945), (2.581, 3.032), (3.116, 3.207),
          (3.330, 3.596), (4.187, 4.300), (4.493, 4.631), (4.799, 4.896), (4.997, 5.235),
          (6.033, 6.252)]
HALF_RATE = 20.0  # km per Myr  (= 2 cm/yr)
H = 3.0           # km, sensor-to-layer distance


def polarity(age):
    return 1.0 if any(a <= age < b for a, b in NORMAL) else -1.0


def anomaly(xs, dx):
    grid = [i * dx for i in range(int(-200 / dx), int(200 / dx) + 1)]
    mag = [polarity(abs(x) / HALF_RATE) for x in grid]
    out = []
    for x in xs:
        s = 0.0
        for xp, m in zip(grid, mag):
            u = x - xp
            s += m * (H * H - u * u) / (u * u + H * H) ** 2
        out.append(s * dx)
    return out


def figure():
    W, Hh = 1800, 640
    x0, x1 = 120, 1760
    X = lambda km: x0 + (km + 120) / 240 * (x1 - x0)
    xs = [i * 0.5 for i in range(-240, 241)]
    an = anomaly(xs, 0.1)
    amax = max(abs(a) for a in an)
    ya, yh = 165, 125  # anomaly panel centre and half-height
    pts = " ".join("%.1f,%.1f" % (X(x), ya - a / amax * yh) for x, a in zip(xs, an))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" viewBox="0 0 {W} {Hh}">',
         f'<rect width="{W}" height="{Hh}" fill="#0C2240"/>',
         '<style>text{font-family:Arial,"Liberation Sans",sans-serif;fill:#E6EDF4}</style>']
    # anomaly panel
    o.append(f'<line x1="{x0}" y1="{ya}" x2="{x1}" y2="{ya}" stroke="#5D7896" stroke-width="1.5" stroke-dasharray="6 6"/>')
    o.append(f'<polyline points="{pts}" fill="none" stroke="#2EE6D6" stroke-width="3" stroke-linejoin="round"/>')
    o.append(f'<text x="{x0 - 16}" y="{ya - yh + 8}" font-size="22" text-anchor="end">+</text>')
    o.append(f'<text x="{x0 - 16}" y="{ya + yh}" font-size="22" text-anchor="end">−</text>')
    o.append(f'<text transform="translate(40 {ya}) rotate(-90)" font-size="22" text-anchor="middle">Anomaly</text>')
    # stripes (map view strip)
    ys, hs = 320, 90
    step = 0.05
    km = -120.0
    while km < 120:
        k2 = km + step
        p = polarity(abs((km + k2) / 2) / HALF_RATE)
        o.append(f'<rect x="{X(km):.2f}" y="{ys}" width="{X(k2) - X(km) + 0.6:.2f}" height="{hs}" '
                 f'fill="{"#1B2531" if p > 0 else "#D7E0EA"}"/>')
        km = k2
    o.append(f'<rect x="{x0}" y="{ys}" width="{x1 - x0}" height="{hs}" fill="none" stroke="#6F8BA8" stroke-width="2"/>')
    # chron names (right flank)
    for name, a, b in (("Brunhes", 0, 0.781), ("Matuyama", 0.781, 2.581), ("Gauss", 2.581, 3.596), ("Gilbert", 3.596, 6.0)):
        cx = X((a + b) / 2 * HALF_RATE)
        o.append(f'<text x="{cx:.1f}" y="{ys - 12}" font-size="18" fill="#9FB3C8" text-anchor="middle">{name}</text>')
    # ridge axis
    o.append(f'<line x1="{X(0)}" y1="20" x2="{X(0)}" y2="{ys + hs}" stroke="#FF8A1F" stroke-width="4"/>')
    o.append(f'<text x="{X(0) + 12}" y="40" font-size="20" fill="#FFC15A">Ridge axis</text>')
    # axes
    for i, (y, label, fn) in enumerate(((462, "Distance from ridge axis (km)", lambda k: "%d" % abs(k)),
                                         (548, "Age of seafloor at 2 cm/yr (Ma)", lambda k: "%g" % (abs(k) / HALF_RATE)))):
        o.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="#9FB3C8" stroke-width="2"/>')
        for k in range(-120, 121, 20):
            o.append(f'<line x1="{X(k)}" y1="{y}" x2="{X(k)}" y2="{y + 8}" stroke="#9FB3C8" stroke-width="2"/>')
            o.append(f'<text x="{X(k)}" y="{y + 32}" font-size="20" text-anchor="middle">{fn(k)}</text>')
        o.append(f'<text x="{x0 - 44}" y="{y + 32}" font-size="20" text-anchor="end" fill="#9FB3C8">{"km" if i == 0 else "Ma"}</text>')
        o.append(f'<text x="{(x0 + x1) / 2}" y="{y + 62}" font-size="20" fill="#9FB3C8" text-anchor="middle">{label}</text>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "simulated_magnetic_anomaly_profile.svg")
    open(p, "w").write(figure())
    print(p)
