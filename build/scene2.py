"""Version-2 visual template ("documentary" style).

Near-black navy background, planet-limb title card, textured geology
(Voronoi rock cells for rigid lithosphere, flow streaks for the
asthenosphere), term + descriptor labels with thin leader lines,
"schematic" tag, clean reference page.  Rendered with render.js --seq.
"""
import json
import math
import os
import random

from scene import (W, H, CX, poly, rect, ellipse, text, rich, group, solid, grad, line,
                   fade_in, fade_out, wipe_in, split_out, move, arrow_pts, double_arrow_pts,
                   chevron_up_pts, Section, REFERENCES)

BG = "0A0F1A"
INK, MUTED, DIM = "F2F4F7", "9AA6B5", "6B7788"
CYAN, LIME, ORANGE = "4FC3F7", "B6F36B", "FF9A3C"
FONT_CSS = "Inter, 'Liberation Sans', Arial, sans-serif"

rng = random.Random(11)


# ------------------------------------------------------------------ helpers
def T(name, s, x, y, w, h, px, color=INK, weight=400, align="l", fx=None, ls=None, a=1.0):
    d = text(name, s, x, y, w, h, px / 2, color=color, align=align, fx=fx or [], a=a)
    d["weight"] = weight
    if ls:
        d["ls"] = ls
    return d


def clip_poly(poly_pts, a, b, c):
    """Keep the part of a convex polygon where a*x + b*y <= c."""
    out = []
    n = len(poly_pts)
    for i in range(n):
        p, q = poly_pts[i], poly_pts[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            out.append(p)
        if fp * fq < 0:
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def voronoi(x0, y0, x1, y1, cell, seed):
    """Voronoi cells (convex polygons) of jittered grid points inside a box."""
    r = random.Random(seed)
    pts = []
    yy = y0 - cell
    row = 0
    while yy < y1 + cell:
        xx = x0 - cell + (cell / 2 if row % 2 else 0)
        while xx < x1 + cell:
            pts.append((xx + r.uniform(-0.35, 0.35) * cell, yy + r.uniform(-0.35, 0.35) * cell))
            xx += cell
        yy += cell * 0.87
        row += 1
    cells = []
    for i, p in enumerate(pts):
        if not (x0 - cell / 2 <= p[0] <= x1 + cell / 2 and y0 - cell / 2 <= p[1] <= y1 + cell / 2):
            continue
        poly_ = [(p[0] - 2 * cell, p[1] - 2 * cell), (p[0] + 2 * cell, p[1] - 2 * cell),
                 (p[0] + 2 * cell, p[1] + 2 * cell), (p[0] - 2 * cell, p[1] + 2 * cell)]
        for j, q in enumerate(pts):
            if i == j or abs(q[0] - p[0]) > 2.2 * cell or abs(q[1] - p[1]) > 2.2 * cell:
                continue
            a, b = q[0] - p[0], q[1] - p[1]
            c = (q[0] ** 2 + q[1] ** 2 - p[0] ** 2 - p[1] ** 2) / 2
            poly_ = clip_poly(poly_, a, b, c)
            if not poly_:
                break
        if len(poly_) >= 3:
            # shrink slightly towards the seed: gives the "grouted" look
            cx_ = sum(v[0] for v in poly_) / len(poly_)
            cy_ = sum(v[1] for v in poly_) / len(poly_)
            cells.append([(cx_ + (v[0] - cx_) * 0.93, cy_ + (v[1] - cy_) * 0.93) for v in poly_])
    return cells


def shade(hex_, k):
    v = int(hex_, 16)
    ch = [min(255, max(0, int(((v >> s) & 255) * k))) for s in (16, 8, 0)]
    return "%02X%02X%02X" % tuple(ch)


def textured(name, outline, base, mortar, cell, seed, vary=0.12):
    """Rock texture: mortar-coloured outline, Voronoi cells, clipped to the outline."""
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    kids = [poly(name + " base", outline, fill=solid(mortar))]
    r = random.Random(seed + 1)
    for i, c in enumerate(voronoi(min(xs), min(ys), max(xs), max(ys), cell, seed)):
        kids.append(poly(f"{name} cell", c, fill=solid(shade(base, 1 + r.uniform(-vary, vary)))))
    g = group(name, kids)
    g["clip"] = [[round(x, 1), round(y, 1)] for x, y in outline]
    return g


def leader(name, x0, y0, x1, y1, fx=None, color=INK):
    """Thin leader line from the label (x0,y0) to the target, with a dot at the target."""
    kids = [poly(name + " line", [(x0, y0), (x1, y1)], closed=False, ln=line(color, 2, 0.85)),
            ellipse(name + " dot", x1, y1, 6, 6, fill=solid(color))]
    return group(name, kids, fx=fx or [])


def label(name, term, desc, x, y, align="l", term_color=INK, fx=None, w=520):
    ax = {"l": x, "r": x - w, "ctr": x - w / 2}[align]
    kids = [T(name + " term", term, ax, y, w, 50, 40, color=term_color, weight=600, align=align)]
    if desc:
        kids.append(T(name + " desc", desc, ax, y + 46, w, 36, 27, color=MUTED, align=align))
    return group(name, kids, fx=fx or [])


def tag(s, fx=None):
    w = 22 * len(s) * 0.52 + 36
    return group("Tag", [rect("Tag bg", 60, 40, w, 44, r=6, fill=solid("0A0F1A", 0.72), ln=line("FFFFFF", 1, 0.18)),
                         T("Tag text", s, 78, 40, w, 44, 22, color="C9D1DB")], fx=fx or [])


def background():
    return [rect("Background", 0, 0, W, H, fill=grad([(0, BG, 1), (1, "0D2236", 1)], 90))]


def streaks(name, x0, y0, x1, y1, n, color, a, seed, curve=0.0):
    r = random.Random(seed)
    kids = []
    for i in range(n):
        y = r.uniform(y0, y1)
        x = r.uniform(x0 - 200, x1)
        L = r.uniform(60, 260)
        pts = [(x + L * k / 6, y + curve * ((x + L * k / 6) - CX) / 960 * 30 + r.uniform(-1, 1)) for k in range(7)]
        kids.append(poly(f"{name} {i}", pts, closed=False, ln=line(color, 1.6, a * r.uniform(0.5, 1))))
    return group(name, kids)


# ------------------------------------------------------------------ slides
def slide_title():
    shapes = [rect("Background", 0, 0, W, H, fill=grad([(0, "070B14", 1), (0.6, BG, 1), (1, "0B1A2C", 1)], 90))]
    R, cy = 2300, 840 + 2300  # planet limb: top of the circle at y = 840
    arc = [(CX + R * math.sin(a), cy - R * math.cos(a)) for a in [i * 0.0045 for i in range(-120, 121)]]
    atmos = ellipse("Atmosphere glow", CX, cy, R + 170, R + 170,
                    fill=grad([(0, "3FA6E0", 0.0), (0.03, "3FA6E0", 0.30), (0.08, "3FA6E0", 0.0)], 90), soft=60)
    ocean = ellipse("Ocean planet", CX, cy, R, R, fill=grad([(0, "1E5E8C", 1), (0.05, "0F3556", 1), (0.12, "081C30", 1)], 90))
    tex = streaks("Ocean texture", 0, 860, W, 1080, 40, "8FC7EA", 0.28, 5, curve=1.0)
    tex["clip"] = [[round(x, 1), round(y, 1)] for x, y in arc] + [[W, H], [0, H]]
    rim = poly("Rim", arc, closed=False, ln=line("E8F4FF", 3, 0.9))
    shapes.append(group("Planet", [atmos, ocean, tex, rim], fx=[fade_in(0.0, 1.2), move(0.0, 6.5, 0, -18)]))
    shapes.append(T("Title", "Spreading Rates", 0, 270, W, 110, 96, weight=600, align="ctr", fx=[fade_in(0.3, 0.8)]))
    shapes.append(rect("Underline", CX - 60, 392, 120, 5, r=2, fill=solid(CYAN), fx=[split_out(0.8, 0.6)]))
    shapes.append(T("Name", "Edwin Wang", 0, 440, W, 60, 46, align="ctr", fx=[fade_in(1.2, 0.6)]))
    shapes.append(T("Student number", "25092450", 0, 506, W, 50, 36, color=MUTED, align="ctr", fx=[fade_in(1.6, 0.6)]))
    return dict(name="Title", adv=6.8, transition=0, shapes=shapes)


def cross_section(prefix, S, G=0, with_magma=True, cells=True):
    """Background, asthenosphere, magma, new-crust group, plates. Returns (shapes, plate ids)."""
    sh = background()
    sh.append(streaks("Water lines", 0, 420, W, 760, 18, "6FB7E0", 0.07, 3))
    # asthenosphere: flowing hot mantle
    xs = S.xs(-20, W + 20, 8)
    top = [(x, S.asth_top(abs(x - CX))) for x in xs]
    asth_pts = top + [(W + 20, H + 20), (-20, H + 20)]
    asth = poly("Asthenosphere", asth_pts, fill=grad([(0, "B3612A", 1), (1, "5C2812", 1)], 90))
    st = streaks("Mantle flow", 0, 680, W, 1080, 70, "FFC48A", 0.22, 9, curve=-1.5)
    st["clip"] = [[round(x, 1), round(y, 1)] for x, y in asth_pts]
    sh.append(group("Asthenosphere (flowing mantle)", [asth, st]))
    if with_magma:
        melt = poly("Magma", [(CX, 652), (CX + 210, 1080), (CX - 210, 1080)],
                    fill=grad([(0, "FFD08A", 0.95), (0.3, ORANGE, 0.75), (1, ORANGE, 0.0)], 90),
                    glow={"color": ORANGE, "r": 22, "a": 0.45})
        sh.append(group("Rising magma", [melt], fx=[wipe_in(0.4, 1.2, "up")]))
    return sh


def mantle_col(S, y):
    """Colour of the asthenosphere gradient at depth y (matches its polygon bbox)."""
    y_top = min(S.asth_top(abs(x - CX)) for x in S.xs(-20, W + 20, 8))
    f = max(0.0, min(1.0, (y - y_top) / (H + 20 - y_top)))
    a, b = int("B3612A", 16), int("5C2812", 16)
    return "%02X%02X%02X" % tuple(round(((a >> k) & 255) * (1 - f) + ((b >> k) & 255) * f) for k in (16, 8, 0))


def plate(S, side, seed):
    sgn = -1 if side == "L" else 1
    xs = S.xs(CX, CX + sgn * 1300, 10)
    top = [(x, S.sf(abs(x - CX))) for x in xs]
    cb = [(x, S.sf(abs(x - CX)) + S.ct) for x in xs]
    lab = [(x, S.lab(abs(x - CX))) for x in xs]
    litho = textured(f"{side} lithospheric mantle", cb + lab[::-1], "6A3A26", "3A1E12", 46, seed)
    crust = textured(f"{side} oceanic crust", top + cb[::-1], "56606E", "2A3039", 26, seed + 7, vary=0.10)
    rim = poly(f"{side} seafloor line", top, closed=False, ln=line("E8EEF5", 2.5, 0.9))
    return [litho, crust, rim]


def slide_spreading(dur=12.4, closing=False):
    """Definition + half/full rates (intro) or a short spreading recap (closing)."""
    G = 150
    S = Section(crest=610, k=5.0, ct=40, lk=7.0, gap=G)
    sh = cross_section("X", S, G)
    T0, TD = (1.6, 3.6) if not closing else (0.8, 3.6)
    # new crust (lighter, fresh basalt) + upwelling mantle beneath
    GX = G + 40
    xs = S.xs(-GX, GX, 8)
    up = poly("Upwelling mantle", [(CX - GX, S.crest + S.ct), (CX + GX, S.crest + S.ct)] +
              [(CX + x, S.lab(abs(x))) for x in xs[::-1]],
              fill=grad([(0, mantle_col(S, S.crest + S.ct), 1), (1, mantle_col(S, S.lab(GX)), 1)], 90))
    nc = textured("New oceanic crust", [(CX - G, S.crest), (CX + G, S.crest), (CX + G, S.crest + S.ct), (CX - G, S.crest + S.ct)],
                  "8794A6", "3A4350", 22, 41, vary=0.08)
    ncl = poly("New crust top", [(CX - G, S.crest), (CX + G, S.crest)], closed=False, ln=line("E8EEF5", 2.5, 0.9))
    sh.insert(-1, group("New crust forming", [up, nc, ncl], fx=[split_out(T0, TD)]))
    sh.append(ellipse("Axial magma", CX, S.crest + S.ct + 10, 44, 10, fill=solid("FFD08A"),
                      glow={"color": ORANGE, "r": 14, "a": 0.7}, fx=[fade_in(1.0, 0.4)]))
    sh.append(group("Left plate", plate(S, "L", 3), fx=[move(T0, TD, -G)]))
    sh.append(group("Right plate", plate(S, "R", 5), fx=[move(T0, TD, G)]))
    sh.append(tag("Schematic · not to scale", fx=[fade_in(0.4, 0.5)]))
    if closing:
        sh.append(label("New crust label", "New oceanic crust", "forms at the ridge axis", 1250, 470,
                        fx=[fade_in(2.6, 0.5)]))
        sh.append(leader("New crust leader", 1240, 500, CX + 60, S.crest + 12, fx=[fade_in(2.6, 0.5)]))
        sh.append(label("Magma label", "Magma", "rising mantle melts", 1250, 830, term_color="FFC48A",
                        fx=[fade_in(1.2, 0.5)]))
        sh.append(leader("Magma leader", 1240, 860, CX + 70, 820, fx=[fade_in(1.2, 0.5)], color="FFC48A"))
        return dict(name="Spreading recap", adv=5.5, transition=0, shapes=sh)
    out = [fade_out(5.5, 0.4)]
    sh.append(label("Ridge label", "Mid-ocean ridge", "where plates separate", CX, 262, align="ctr",
                    fx=[fade_in(0.4, 0.5)] + out))
    sh.append(leader("Ridge leader", CX, 360, CX, S.crest - 8, fx=[fade_in(0.5, 0.5)] + out))
    sh.append(label("Plate label", "Oceanic plate", "moves away from the ridge", 150, 330,
                    fx=[fade_in(1.6, 0.5)] + out))
    sh.append(leader("Plate leader", 300, 420, 470, S.sf(490) - 6, fx=[fade_in(1.6, 0.5)] + out))
    sh.append(label("New crust label", "New oceanic crust", "forms at the axis", 1400, 330,
                    fx=[fade_in(3.6, 0.5)] + out))
    sh.append(leader("New crust leader", 1500, 420, CX + 90, S.crest + 10, fx=[fade_in(3.6, 0.5)] + out))
    # half / full rates
    ya, xl, xr = 520, 560, 1360
    sh.append(poly("Half arrow left", arrow_pts(CX - 6, ya, xl, ya, 14, 44, 40), fill=solid(CYAN), fx=[wipe_in(5.9, 0.7, "left")]))
    sh.append(poly("Half arrow right", arrow_pts(CX + 6, ya, xr, ya, 14, 44, 40), fill=solid(CYAN), fx=[wipe_in(6.4, 0.7, "right")]))
    sh.append(label("Half label", "Half-spreading rate", "one plate, relative to the ridge", 150, 430, term_color=CYAN,
                    fx=[fade_in(6.0, 0.5)]))
    sh.append(poly("Full arrow", double_arrow_pts(xl, xr, 300, 12, 44, 40), fill=solid(LIME), fx=[split_out(7.3, 0.8)]))
    sh.append(label("Full label", "Full-spreading rate", "separation of the two plates", CX, 160, align="ctr",
                    term_color=LIME, w=800, fx=[fade_in(7.5, 0.5)]))
    sh.append(T("Half value L", "2 cm/yr", CX - 400, 548, 400 - 10, 50, 36, color=CYAN, weight=600, align="ctr", fx=[fade_in(8.5, 0.5)]))
    sh.append(T("Half value R", "2 cm/yr", CX + 10, 548, 400 - 10, 50, 36, color=CYAN, weight=600, align="ctr", fx=[fade_in(8.6, 0.5)]))
    sh.append(T("Full value", "4 cm/yr", CX - 200, 320, 400, 50, 36, color=LIME, weight=600, align="ctr", fx=[fade_in(8.9, 0.5)]))
    sh.append(T("Symmetric note", "symmetric example: 2 + 2 = 4", 1300, 40, 560, 44, 24, color="C9D1DB", align="r",
                fx=[fade_in(9.2, 0.5)]))
    return dict(name="Spreading rate", adv=dur, transition=0, shapes=sh)


def stripes_geometry():
    widths = [100, 140, 70, 120, 100]
    pol = ["N", "R", "N", "R", "N"]
    return widths, pol


def slide_stripes(dur, form=True, paper=False, teaser=False):
    """Map view of a ridge with magnetic stripes."""
    sh = background()
    y0, h = 330, 380
    widths, pol = stripes_geometry()
    span = sum(widths)
    N, R = "1A222E", "DCE3EC"
    sh.append(textured("Seafloor (map view)", [(CX - span - 40, y0), (CX + span + 40, y0), (CX + span + 40, y0 + h), (CX - span - 40, y0 + h)],
                       "33465C", "1E2A38", 40, 77, vary=0.06))
    if form:
        v = span / 2.8
        t, births = 0.5, []
        for w in widths:
            births.append((t, w / v)); t += w / v
        t_end = t
        out = [fade_out(4.0, 0.7)] if paper else []
        for i, (w, p) in enumerate(zip(widths, pol)):
            tb, db = births[i]
            later = sum(widths[i + 1:])
            for side in ("L", "R"):
                sgn = -1 if side == "L" else 1
                x = CX - w if side == "L" else CX
                fx = [wipe_in(tb, db, "left" if side == "L" else "right")]
                if later:
                    fx.append(move(tb + db, t_end - (tb + db), sgn * later))
                sh.append(rect(f"Band {i+1} {side}", x, y0, w, h, fill=solid(N if p == "N" else R, 0.95), fx=fx + out))
    else:
        off = 0
        for w, p in list(zip(widths, pol))[::-1]:
            for side in ("L", "R"):
                x = CX - off - w if side == "L" else CX + off
                sh.append(rect("Band", x, y0, w, h, fill=solid(N if p == "N" else R, 0.95)))
            off += w
    axis_out = [fade_out(4.0, 0.7)] if paper else []
    sh.append(poly("Ridge axis", [(CX, y0 - 20), (CX, y0 + h + 20)], closed=False, ln=line(ORANGE, 5),
                   glow={"color": ORANGE, "r": 10, "a": 0.6}, fx=axis_out))
    sh.append(label("Ridge label", "Mid-ocean ridge", "new crust forms here", CX, 205, align="ctr",
                    fx=[fade_in(0.1, 0.5)] + axis_out))
    if teaser:
        sh.append(label("Stripes label", "Magnetic stripes", "a record written in the seafloor", 150, 790,
                        fx=[fade_in(0.2, 0.5)]))
        return dict(name="Measuring teaser", adv=dur, transition=0, shapes=sh)
    lg = [fade_in(2.4, 0.5)] + axis_out
    sh.append(rect("Legend N", 600, 790, 44, 28, fill=solid(N), ln=line("8FA6BE", 1.5), fx=lg))
    sh.append(T("Legend N text", "Normal polarity", 658, 784, 360, 40, 30, color="C9D1DB", fx=lg))
    sh.append(rect("Legend R", 1010, 790, 44, 28, fill=solid(R), fx=lg))
    sh.append(T("Legend R text", "Reversed polarity", 1068, 784, 380, 40, 30, color="C9D1DB", fx=lg))
    sh.append(tag("Map view · schematic", fx=[fade_in(0.2, 0.5)] + axis_out))
    if paper:
        py0, ph = 400, 240
        kids = []
        for side in ("L", "R"):
            x0 = CX - span if side == "L" else CX
            kids.append(rect(f"Paper shadow {side}", x0 + 10, py0 + 14, span, ph, fill=solid("000000", 0.35), soft=10))
            kids.append(rect(f"Paper strip {side}", x0, py0, span, ph, fill=solid("F4F1E8"), ln=line("C9C3B5", 1.5)))
            off = 0
            for w, p in list(zip(widths, pol))[::-1]:
                if p == "N":
                    x = CX - off - w if side == "L" else CX + off
                    kids.append(rect("Paper stripe", x, py0, w, ph, fill=solid("141414")))
                off += w
        sh.append(group("Paper strip model", kids, fx=[fade_in(4.1, 0.8)]))
        sh.append(rect("Cardboard ridge", CX - 34, py0 - 60, 68, ph + 120, r=6,
                       fill=grad([(0, "C9A574", 1), (1, "A9845A", 1)], 0), ln=line("7A5A38", 3), fx=[fade_in(4.1, 0.8)]))
        sh.append(label("Model label", "My paper model", "same pattern, same ridge", CX, 760, align="ctr",
                        fx=[fade_in(4.5, 0.6)]))
    return dict(name="Magnetic stripes" + (" to model" if paper else ""), adv=dur, transition=0, shapes=sh)


def slide_refs():
    sh = [rect("Background", 0, 0, W, H, fill=solid(BG))]
    sh.append(T("Heading", "References", 150, 92, 1200, 70, 56, weight=600))
    sh.append(rect("Heading rule", 150, 168, 90, 4, r=2, fill=solid(CYAN)))
    paras, is_url = [], []
    for runs in REFERENCES:
        main, url = [], []
        for t_, it in runs:
            if "Available at:" in t_:
                pre, post = t_.split("Available at:", 1)
                if pre.strip():
                    main.append((pre.rstrip(), it))
                url.append(("Available at:" + post, 0, "8C99A8"))
            else:
                main.append((t_, it))
        paras.append(main); is_url.append(False)
        if url:
            paras.append(url); is_url.append(True)
    r = rich("Reference list", paras, 150, 215, 1460, 13, color="E9EDF2", line=1.32, gap=0.25)
    y = 0
    for i, p in enumerate(r["paras"]):
        p["y"] = y
        y += 26 * 1.32 * len(p["lines"])
        nxt_is_url = i + 1 < len(is_url) and is_url[i + 1]
        y += 4 if nxt_is_url else 34
    r["h"] = y
    sh.append(r)
    return dict(name="References", adv=3.2, transition=0, shapes=sh)


def build():
    slides = [slide_title(), slide_spreading(), slide_stripes(2.35, form=False, teaser=True),
              slide_spreading(closing=True), slide_stripes(6.0, form=True, paper=True), slide_refs()]
    seqs = {
        "v2_intro": {"xf": 0.5, "segments": [{"slide": 0, "dur": 6.8}, {"slide": 1, "dur": 12.4}, {"slide": 2, "dur": 2.35}]},
        "v2_closing": {"xf": 0.5, "segments": [{"slide": 3, "dur": 5.5}, {"slide": 4, "dur": 6.0}, {"slide": 5, "dur": 3.2}]},
    }
    return dict(W=W, H=H, fps=30, total=0, font="Inter", font_css=FONT_CSS, slides=slides, sequences=seqs)


if __name__ == "__main__":
    sc = build()
    out = os.path.join(os.path.dirname(__file__), "scene2.json")
    json.dump(sc, open(out, "w"))
    for k, v in sc["sequences"].items():
        print(k, sum(s["dur"] for s in v["segments"]) - v["xf"] * (len(v["segments"]) - 1))
