"""Version-3 visuals: v2 template + a light, science-explainer feel.

Changes vs v2 (kept deliberately subtle): an Earth-from-space opening with a
slowly rotating globe and a gentle push-in to the ridge; slightly brighter
ocean/magma colours, faint light rays and a few rising magma bubbles; every
scene drifts with a very slow ~4% camera push.
"""
import json
import math
import os
import random

import scene2 as V2
from scene import (W, H, CX, poly, rect, ellipse, group, solid, grad, line, fade_in, fade_out,
                   wipe_in, split_out, move, Section)
from scene2 import T, textured, leader, label, tag, streaks, mantle_col, plate, BG, MUTED, CYAN, LIME, ORANGE, INK


def zoom(s, d, a, b, cx=CX, cy=540, accel=0.0, decel=0.0):
    return {"type": "zoom", "s": s, "d": d, "from": a, "to": b, "cx": cx, "cy": cy, "accel": accel, "decel": decel}


def rgrad(stops, cx=0.5, cy=0.5, r=0.5, fx=None, fy=None):
    d = {"type": "rgrad", "cx": cx, "cy": cy, "r": r, "stops": [list(s) for s in stops]}
    if fx is not None:
        d["fx"], d["fy"] = fx, fy
    return d


def camera(shapes, dur, k=1.04, cx=CX, cy=560, skip=("Background",)):
    """Very slow push-in applied to every element of a scene (except the background)."""
    for sh in shapes:
        if sh["name"] in skip:
            continue
        sh["fx"] = [zoom(0, dur, 1.0, k, cx, cy)] + sh["fx"]
    return shapes


def blob(cx, cy, r, seed, n=14):
    rr = random.Random(seed)
    radii = [r * rr.uniform(0.7, 1.15) for _ in range(n)]
    pts = []
    for i in range(n * 3):  # smooth by interpolating radii
        a = 2 * math.pi * i / (n * 3)
        j = i / 3
        r0, r1 = radii[int(j) % n], radii[(int(j) + 1) % n]
        f = j - int(j)
        rad = r0 * (1 - f) + r1 * f
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a) * 0.85))
    return pts


# ------------------------------------------------------------------ title: Earth from space
def slide_title(dur=6.8):
    sh = [rect("Background", 0, 0, W, H, fill=rgrad([(0, "101B33", 1), (1, "05080F", 1)], 0.7, 0.5, 0.8))]
    r = random.Random(3)
    stars = []
    for i in range(140):
        x, y = r.uniform(0, W), r.uniform(0, H)
        s = r.choice([1.2, 1.5, 2.0, 2.6])
        stars.append(ellipse(f"Star {i}", x, y, s, s, fill=solid("FFFFFF", r.uniform(0.25, 0.8))))
    sh.append(group("Stars", stars, fx=[fade_in(0.0, 0.8)]))
    gx, gy, R = 1330, 560, 330
    circ = [(gx + R * math.cos(a * math.pi / 90), gy + R * math.sin(a * math.pi / 90)) for a in range(180)]
    atmos = ellipse("Atmosphere", gx, gy, R + 46, R + 46,
                    fill=rgrad([(0.80, "5EC8FF", 0.0), (0.88, "5EC8FF", 0.42), (1.0, "5EC8FF", 0.0)]))
    ocean = ellipse("Ocean", gx, gy, R, R, fill=rgrad([(0, "3AA0E8", 1), (0.55, "1661A8", 1), (1, "0A2F5C", 1)], 0.38, 0.35, 0.75))
    # continents + mid-ocean ridge on a strip that slides left = slow rotation
    land = []
    r2 = random.Random(9)
    for i, (dx, dy, rad) in enumerate([(-560, -150, 120), (-430, 120, 95), (-80, -210, 140), (40, 180, 110),
                                        (430, -60, 150), (620, 200, 90), (900, -170, 120), (1050, 110, 130)]):
        land.append(poly(f"Land {i}", blob(gx + dx, gy + dy, rad, 20 + i), fill=solid(r2.choice(["5FA35A", "7BB661", "C9B27A", "A8C26F"]))))
    ridge_x = gx + 170
    zig = []
    for k in range(13):
        y = gy - R - 20 + k * (2 * R + 40) / 12
        zig.append((ridge_x + 40 * math.sin(k * 0.9) + (14 if k % 2 else -14), y))
    ridge = poly("Mid-ocean ridge", zig, closed=False, ln=line("FFB45A", 5, 0.95), glow={"color": "FF9A3C", "r": 10, "a": 0.7})
    spin = group("Surface", land + [ridge], fx=[move(0, dur, -150, 0)])
    shade = ellipse("Night side", gx, gy, R, R, fill=rgrad([(0.55, "000814", 0.0), (1.0, "000814", 0.65)], 0.30, 0.30, 0.95))
    shine = ellipse("Highlight", gx - 120, gy - 140, 120, 80, fill=solid("FFFFFF", 0.10), soft=50)
    globe = group("Globe", [ocean, spin, shade, shine])
    globe["clip"] = [[round(x, 1), round(y, 1)] for x, y in circ]
    # gentle push-in towards where the ridge ends up (x ~ ridge_x - 150)
    tx = ridge_x - 150
    # screen x = tx + k*(x + dx - tx): bring the ridge (x = tx) to the screen centre as k -> 1.9
    earth = group("Earth", [atmos, globe], fx=[fade_in(0.0, 1.0), zoom(0, dur - 1.0, 1.0, 1.06, tx, gy),
                                                 zoom(dur - 1.0, 1.0, 1.06, 1.9, tx, gy, accel=0.6),
                                                 move(dur - 1.0, 1.0, (CX - tx) / 1.9, 0, accel=0.6)])
    sh.append(earth)
    sh.append(T("Title", "Spreading Rates", 150, 380, 900, 110, 92, weight=700, fx=[fade_in(0.3, 0.8), fade_out(dur - 0.9, 0.5)]))
    sh.append(rect("Underline", 154, 492, 110, 5, r=2, fill=solid(CYAN), fx=[wipe_in(0.8, 0.5, "right"), fade_out(dur - 0.9, 0.5)]))
    sh.append(T("Subtitle", "How fast is the ocean floor moving?", 150, 520, 900, 50, 34, color="BFD3E6",
                fx=[fade_in(1.0, 0.6), fade_out(dur - 0.9, 0.5)]))
    sh.append(T("Name", "Edwin Wang", 150, 640, 700, 50, 38, fx=[fade_in(1.4, 0.6), fade_out(dur - 0.9, 0.5)]))
    sh.append(T("Student number", "25092450", 150, 690, 700, 44, 30, color=MUTED, fx=[fade_in(1.7, 0.6), fade_out(dur - 0.9, 0.5)]))
    return dict(name="Title Earth", adv=dur, transition=0, shapes=sh)


# ------------------------------------------------------------------ cross-section, brighter
def ocean_bg():
    sh = [rect("Background", 0, 0, W, H, fill=grad([(0, "081A33", 1), (0.5, "0E3D6E", 1), (1, "1A6CA6", 1)], 90))]
    rays = []
    r = random.Random(4)
    for i in range(5):
        x = r.uniform(200, 1700)
        w = r.uniform(60, 140)
        rays.append(poly(f"Light ray {i}", [(x, -10), (x + w, -10), (x + w * 2.4 - 200, 760), (x - 200, 760)],
                         fill=grad([(0, "BFE6FF", 0.10), (1, "BFE6FF", 0.0)], 90)))
    sh.append(group("Light rays", rays, fx=[move(0, 14, 60, 0)]))
    return sh


def bubbles(t0, t1, seed, n=10):
    r = random.Random(seed)
    out = []
    for i in range(n):
        s = r.uniform(t0, t1 - 1.6)
        x = CX + r.uniform(-120, 120)
        y = r.uniform(960, 1060)
        rad = r.uniform(5, 10)
        out.append(ellipse(f"Bubble {i}", x, y, rad, rad, fill=solid("FFE3A0", 0.85), glow={"color": "FFB45A", "r": 6, "a": 0.6},
                           fx=[fade_in(s, 0.3), move(s, 1.6, r.uniform(-20, 20) - (x - CX) * 0.4, -r.uniform(200, 300)), fade_out(s + 1.2, 0.4)]))
    return out


def section_scene(dur, closing=False):
    G = 150
    S = Section(crest=610, k=5.0, ct=40, lk=7.0, gap=G)
    sh = ocean_bg()
    xs = S.xs(-20, W + 20, 8)
    top = [(x, S.asth_top(abs(x - CX))) for x in xs]
    asth_pts = top + [(W + 20, H + 20), (-20, H + 20)]
    asth = poly("Asthenosphere", asth_pts, fill=grad([(0, "B3612A", 1), (1, "5C2812", 1)], 90))
    st = streaks("Mantle flow", 0, 680, W, 1080, 70, "FFC48A", 0.24, 9, curve=-1.5)
    st["clip"] = [[round(x, 1), round(y, 1)] for x, y in asth_pts]
    sh.append(group("Asthenosphere (flowing mantle)", [asth, st]))
    melt = poly("Magma", [(CX, 652), (CX + 210, 1080), (CX - 210, 1080)],
                fill=grad([(0, "FFE08A", 1.0), (0.3, "FF8A2A", 0.8), (1, "FF8A2A", 0.0)], 90),
                glow={"color": "FF8A2A", "r": 26, "a": 0.5})
    sh.append(group("Rising magma", [melt], fx=[wipe_in(0.4, 1.2, "up")]))
    sh += bubbles(1.2, dur, 12 if not closing else 13, 12 if not closing else 8)
    T0, TD = (1.6, 3.6) if not closing else (0.8, 3.6)
    GX = G + 40
    xs2 = S.xs(-GX, GX, 8)
    up = poly("Upwelling mantle", [(CX - GX, S.crest + S.ct), (CX + GX, S.crest + S.ct)] + [(CX + x, S.lab(abs(x))) for x in xs2[::-1]],
              fill=grad([(0, mantle_col(S, S.crest + S.ct), 1), (1, mantle_col(S, S.lab(GX)), 1)], 90))
    nc = textured("New oceanic crust", [(CX - G, S.crest), (CX + G, S.crest), (CX + G, S.crest + S.ct), (CX - G, S.crest + S.ct)],
                  "8E9CB0", "3A4350", 22, 41, vary=0.08)
    ncl = poly("New crust top", [(CX - G, S.crest), (CX + G, S.crest)], closed=False, ln=line("E8EEF5", 2.5, 0.9))
    sh.append(group("New crust forming", [up, nc, ncl], fx=[split_out(T0, TD)]))
    sh.append(ellipse("Axial magma", CX, S.crest + S.ct + 10, 44, 10, fill=solid("FFE08A"),
                      glow={"color": "FF8A2A", "r": 16, "a": 0.8}, fx=[fade_in(1.0, 0.4)]))
    sh.append(group("Left plate", plate(S, "L", 3), fx=[move(T0, TD, -G)]))
    sh.append(group("Right plate", plate(S, "R", 5), fx=[move(T0, TD, G)]))
    return S, sh


def slide_spreading(dur=12.4):
    S, sh = section_scene(dur)
    camera(sh, dur, 1.04, CX, 560)
    sh.append(tag("Schematic · not to scale", fx=[fade_in(0.4, 0.5)]))
    out = [fade_out(5.5, 0.4)]
    sh.append(label("Ridge label", "Mid-ocean ridge", "where plates separate", CX, 262, align="ctr", fx=[fade_in(0.4, 0.5)] + out))
    sh.append(leader("Ridge leader", CX, 360, CX, S.crest - 8, fx=[fade_in(0.5, 0.5)] + out))
    sh.append(label("Plate label", "Oceanic plate", "moves away from the ridge", 150, 330, fx=[fade_in(1.6, 0.5)] + out))
    sh.append(leader("Plate leader", 300, 420, 470, S.sf(490) - 6, fx=[fade_in(1.6, 0.5)] + out))
    sh.append(label("New crust label", "New oceanic crust", "forms at the axis", 1400, 330, fx=[fade_in(3.6, 0.5)] + out))
    sh.append(leader("New crust leader", 1500, 420, CX + 90, S.crest + 10, fx=[fade_in(3.6, 0.5)] + out))
    from scene import arrow_pts, double_arrow_pts
    ya, xl, xr = 520, 560, 1360
    sh.append(poly("Half arrow left", arrow_pts(CX - 6, ya, xl, ya, 14, 44, 40), fill=solid(CYAN), fx=[wipe_in(5.9, 0.7, "left")]))
    sh.append(poly("Half arrow right", arrow_pts(CX + 6, ya, xr, ya, 14, 44, 40), fill=solid(CYAN), fx=[wipe_in(6.4, 0.7, "right")]))
    sh.append(label("Half label", "Half-spreading rate", "one plate, relative to the ridge", 150, 430, term_color=CYAN, fx=[fade_in(6.0, 0.5)]))
    sh.append(poly("Full arrow", double_arrow_pts(xl, xr, 300, 12, 44, 40), fill=solid(LIME), fx=[split_out(7.3, 0.8)]))
    sh.append(label("Full label", "Full-spreading rate", "separation of the two plates", CX, 160, align="ctr", term_color=LIME, w=800,
                    fx=[fade_in(7.5, 0.5)]))
    sh.append(T("Half value L", "2 cm/yr", CX - 400, 548, 390, 50, 36, color=CYAN, weight=600, align="ctr", fx=[fade_in(8.5, 0.5)]))
    sh.append(T("Half value R", "2 cm/yr", CX + 10, 548, 390, 50, 36, color=CYAN, weight=600, align="ctr", fx=[fade_in(8.6, 0.5)]))
    sh.append(T("Full value", "4 cm/yr", CX - 200, 320, 400, 50, 36, color=LIME, weight=600, align="ctr", fx=[fade_in(8.9, 0.5)]))
    sh.append(T("Symmetric note", "symmetric example: 2 + 2 = 4", 1300, 40, 560, 44, 24, color="C9D1DB", align="r", fx=[fade_in(9.2, 0.5)]))
    return dict(name="Spreading rate", adv=dur, transition=0, shapes=sh)


def slide_recap(dur=5.5):
    S, sh = section_scene(dur, closing=True)
    camera(sh, dur, 1.04, CX, 600)
    sh.append(tag("Schematic · not to scale", fx=[fade_in(0.4, 0.5)]))
    sh.append(label("New crust label", "New oceanic crust", "forms at the ridge axis", 1250, 470, fx=[fade_in(2.6, 0.5)]))
    sh.append(leader("New crust leader", 1240, 500, CX + 60, S.crest + 12, fx=[fade_in(2.6, 0.5)]))
    sh.append(label("Magma label", "Magma", "rising mantle melts", 1250, 830, term_color="FFC48A", fx=[fade_in(1.2, 0.5)]))
    sh.append(leader("Magma leader", 1240, 860, CX + 70, 820, fx=[fade_in(1.2, 0.5)], color="FFC48A"))
    return dict(name="Spreading recap", adv=dur, transition=0, shapes=sh)


def stripes(dur, **kw):
    sl = V2.slide_stripes(dur, **kw)
    sl["shapes"][0] = rect("Background", 0, 0, W, H, fill=grad([(0, "081A33", 1), (1, "123F6B", 1)], 90))
    camera(sl["shapes"], dur, 1.035, CX, 520)
    return sl


def build():
    slides = [slide_title(), slide_spreading(), stripes(2.35, form=False, teaser=True),
              slide_recap(), stripes(6.0, form=True, paper=True), V2.slide_refs()]
    seqs = {
        "v3_intro": {"xf": 0.5, "segments": [{"slide": 0, "dur": 6.8}, {"slide": 1, "dur": 12.4}, {"slide": 2, "dur": 2.35}]},
        "v3_closing": {"xf": 0.5, "segments": [{"slide": 3, "dur": 5.5}, {"slide": 4, "dur": 6.0}, {"slide": 5, "dur": 3.2}]},
    }
    return dict(W=W, H=H, fps=30, total=0, font="Inter", font_css=V2.FONT_CSS, slides=slides, sequences=seqs)


if __name__ == "__main__":
    sc = build()
    json.dump(sc, open(os.path.join(os.path.dirname(__file__), "scene3.json"), "w"))
    for k, v in sc["sequences"].items():
        print(k, sum(s["dur"] for s in v["segments"]) - v["xf"] * (len(v["segments"]) - 1))
