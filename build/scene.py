"""Single source of truth for the 'Spreading Rates' animation.

Defines every shape (geometry, colour) and every animation effect (type, start,
duration) for the four slides.  `make_pptx.py` turns this into native PowerPoint
shapes + OOXML animation timing; `render.js` plays the *same* timeline frame by
frame to produce the MP4 and PNGs.

Coordinates are pixels on a 1920 x 1080 canvas (1 px = 6350 EMU on a 13.333" x
7.5" slide).  Effect times are seconds from the moment the slide's transition
has finished (this is when PowerPoint starts a slide's animations).
"""
import json
import math
import os

W, H = 1920, 1080
CX = 960

# ---------------------------------------------------------------- palette
C = dict(
    bg_top="05122A", bg_bot="0B2C4E",
    text="F2F6FA", muted="9FB3C8",
    crust="5E6E80", crust_edge="8796A8", crust_new="A7B4C2",
    litho="5A2C1A", asth_top="9A4A22", asth_bot="5E2814",
    magma="FF8A1F", magma_hot="FFC15A",
    cyan="2EE6D6", cyan_soft="7FF3E8",
    pill="061A33",
    normal="1B2531", reversed="D7E0EA", panel="35506E",
    paper="F4F1E8", ink="141414", cardboard="A9845A", cardboard_dark="7A5A38",
)

FONT = "Arial"


# ---------------------------------------------------------------- helpers
def solid(color, a=1.0):
    return {"type": "solid", "color": color, "a": a}


def grad(stops, angle=90):
    """stops: [(pos 0..1, color, alpha)]; angle in degrees, 90 = top->bottom."""
    return {"type": "grad", "angle": angle, "stops": [list(s) for s in stops]}


def line(color, w=2, a=1.0, dash=None):
    return {"color": color, "w": w, "a": a, "dash": dash}


def bbox_of(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]


def poly(name, pts, fill=None, ln=None, closed=True, glow=None, soft=None, fx=None):
    pts = [[round(x, 2), round(y, 2)] for x, y in pts]
    return dict(kind="poly", name=name, pts=pts, closed=closed, fill=fill, line=ln,
                glow=glow, soft=soft, fx=fx or [], bbox=bbox_of(pts))


def rect(name, x, y, w, h, fill=None, ln=None, r=0, glow=None, soft=None, fx=None):
    return dict(kind="rect", name=name, x=x, y=y, w=w, h=h, r=r, fill=fill, line=ln,
                glow=glow, soft=soft, fx=fx or [], bbox=[x, y, w, h])


def ellipse(name, cx, cy, rx, ry, fill=None, ln=None, glow=None, soft=None, fx=None):
    return dict(kind="ellipse", name=name, x=cx - rx, y=cy - ry, w=2 * rx, h=2 * ry,
                fill=fill, line=ln, glow=glow, soft=soft, fx=fx or [],
                bbox=[cx - rx, cy - ry, 2 * rx, 2 * ry])


def text(name, s, x, y, w, h, size, color=None, bold=False, align="ctr", fx=None, a=1.0):
    return dict(kind="text", name=name, text=s, x=x, y=y, w=w, h=h, size=size,
                color=color or C["text"], bold=bold, align=align, a=a, fx=fx or [],
                bbox=[x, y, w, h])


_FONTS = {}


def _font(bold, italic, px):
    key = (bold, italic, px)
    if key not in _FONTS:
        from PIL import ImageFont
        name = "LiberationSans-" + {(0, 0): "Regular", (1, 0): "Bold", (0, 1): "Italic", (1, 1): "BoldItalic"}[(int(bold), int(italic))]
        _FONTS[key] = ImageFont.truetype("/usr/share/fonts/truetype/liberation/%s.ttf" % name, px)
    return _FONTS[key]


def rich(name, paras, x, y, w, size, color=None, line=1.2, gap=0.55, fx=None):
    """paras: list of paragraphs, each a list of (text, italic) runs.
    Lines are wrapped here with Arial-metric widths (Liberation Sans); PowerPoint
    wraps the same paragraphs itself in a box of the same width."""
    px = size * 2
    lh = px * line
    out, yy = [], 0.0
    for runs in paras:
        words = []
        for t, it in runs:
            for i, tok in enumerate(t.split(" ")):
                if i > 0:
                    words.append((" ", it))
                if tok:
                    words.append((tok, it))
        lines, cur, cw = [], [], 0.0
        for tok, it in words:
            tw = _font(False, it, px).getlength(tok)
            if tok != " " and cur and cw + tw > w * 0.985:
                while cur and cur[-1][0] == " ":
                    cw -= _font(False, cur[-1][1], px).getlength(" "); cur.pop()
                lines.append(cur); cur, cw = [], 0.0
            if tok == " " and not cur:
                continue
            cur.append([tok, it]); cw += tw
        if cur:
            lines.append(cur)
        merged = []
        for ln in lines:  # merge consecutive tokens with same style
            m = []
            for tok, it in ln:
                if m and m[-1][1] == it:
                    m[-1][0] += tok
                else:
                    m.append([tok, it])
            merged.append(m)
        out.append({"runs": [[t, it] for t, it in runs], "lines": merged, "y": yy})
        yy += lh * len(merged) + px * gap
    h = yy - px * gap
    return dict(kind="rich", name=name, x=x, y=y, w=w, h=h, size=size, line=line, gap=gap,
                color=color or C["text"], paras=out, fx=fx or [], bbox=[x, y, w, h])


def group(name, children, fx=None):
    xs, ys, xe, ye = [], [], [], []
    for c in children:
        bx, by, bw, bh = c["bbox"]
        xs.append(bx); ys.append(by); xe.append(bx + bw); ye.append(by + bh)
    bb = [min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys)]
    return dict(kind="group", name=name, children=children, fx=fx or [], bbox=bb)


# effects -------------------------------------------------------------
def fade_in(s, d=0.5):
    return {"type": "fade_in", "s": s, "d": d}


def fade_out(s, d=0.5):
    return {"type": "fade_out", "s": s, "d": d}


def wipe_in(s, d, direction):
    """direction = direction the reveal edge travels: up/down/left/right."""
    return {"type": "wipe_in", "s": s, "d": d, "dir": direction}


def split_out(s, d):
    """Vertical split opening outward from the centre line (barn outVertical)."""
    return {"type": "split_out", "s": s, "d": d}


def move(s, d, dx, dy=0, accel=0.0, decel=0.0):
    return {"type": "move", "s": s, "d": d, "dx": dx, "dy": dy, "accel": accel, "decel": decel}


def arrow_pts(x0, y0, x1, y1, shaft=14, head=40, head_len=38):
    """Single-headed arrow polygon from (x0,y0) to tip (x1,y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    px, py = -uy, ux
    bx, by = x1 - ux * head_len, y1 - uy * head_len
    s, h = shaft / 2, head / 2
    return [
        (x0 + px * s, y0 + py * s), (bx + px * s, by + py * s), (bx + px * h, by + py * h),
        (x1, y1),
        (bx - px * h, by - py * h), (bx - px * s, by - py * s), (x0 - px * s, y0 - py * s),
    ]


def double_arrow_pts(x0, x1, y, shaft=14, head=44, head_len=40):
    s, h = shaft / 2, head / 2
    return [
        (x0, y), (x0 + head_len, y - h), (x0 + head_len, y - s), (x1 - head_len, y - s),
        (x1 - head_len, y - h), (x1, y), (x1 - head_len, y + h), (x1 - head_len, y + s),
        (x0 + head_len, y + s), (x0 + head_len, y + h),
    ]


def chevron_up_pts(cx, cy, w=34, h=20, t=9):
    return [(cx - w / 2, cy + h / 2), (cx, cy - h / 2), (cx + w / 2, cy + h / 2),
            (cx + w / 2 - t * 0.9, cy + h / 2 + t * 0.55), (cx, cy - h / 2 + t * 1.15),
            (cx - w / 2 + t * 0.9, cy + h / 2 + t * 0.55)]


def background():
    return [
        rect("Background", 0, 0, W, H,
             fill=grad([(0, C["bg_top"], 1), (1, C["bg_bot"], 1)], 90)),
        ellipse("Surface light", CX, -120, 1100, 420,
                fill=grad([(0, "4FB3D9", 0.10), (1, "4FB3D9", 0.0)], 90), soft=160),
    ]


# ---------------------------------------------------------------- cross-section geometry
class Section:
    """Ridge cross-section.  Seafloor depth follows a square-root-of-distance
    (i.e. square-root-of-age) subsidence curve; the lithosphere thickens the same way.
    """

    def __init__(self, crest, k, ct, lk, gap=0):
        self.crest, self.k, self.ct, self.lk, self.gap = crest, k, ct, lk, gap

    def sf(self, d):  # seafloor depth at distance d from the ridge axis
        return self.crest + self.k * math.sqrt(max(d, 0))

    def lab(self, d):  # base of lithosphere
        return self.sf(d) + self.ct + self.lk * math.sqrt(max(d, 0))

    def xs(self, x_from, x_to, step=16):
        n = max(2, int(abs(x_to - x_from) / step))
        return [x_from + (x_to - x_from) * i / n for i in range(n + 1)]

    def plate(self, side, prefix, ext=1300):
        """Crust + lithospheric mantle for one plate whose tip sits on the axis."""
        sgn = -1 if side == "L" else 1
        xs = self.xs(CX, CX + sgn * ext)
        top = [(x, self.sf(abs(x - CX))) for x in xs]
        cb = [(x, self.sf(abs(x - CX)) + self.ct) for x in xs]
        lab = [(x, self.lab(abs(x - CX))) for x in xs]
        litho = poly(prefix + " lithospheric mantle", cb + lab[::-1], fill=solid(C["litho"]))
        crust = poly(prefix + " oceanic crust", top + cb[::-1],
                     fill=grad([(0, C["crust_edge"], 1), (0.25, C["crust"], 1), (1, "4C5A6A", 1)], 90),
                     ln=line("9AA9BA", 1.5, 0.6))
        return [litho, crust]

    def asth_top(self, d):
        g = self.gap
        return max(self.sf(d), min(self.sf(d) + self.ct, self.lab(max(d - g, 0))))

    def asthenosphere(self):
        xs = self.xs(-20, W + 20, 8)
        top = [(x, self.asth_top(abs(x - CX))) for x in xs]
        return poly("Asthenospheric mantle", top + [(W + 20, H + 20), (-20, H + 20)],
                    fill=grad([(0, C["asth_top"], 1), (1, C["asth_bot"], 1)], 90))


# ================================================================ SLIDE 1
def slide1():
    S = Section(crest=600, k=5.0, ct=40, lk=7.0)
    shapes = background()
    # cross-section (fades in as one group)
    melt = poly("Melt zone (magma)", [(CX, 652), (CX + 230, 1080), (CX - 230, 1080)],
                fill=grad([(0, C["magma_hot"], 0.85), (0.35, C["magma"], 0.55), (1, C["magma"], 0.0)], 90))
    sec = [S.asthenosphere(), melt] + S.plate("L", "Left plate") + S.plate("R", "Right plate")
    shapes.append(group("Cross-section", sec, fx=[fade_in(0.0, 0.9)]))
    # ridge highlight (soft glow that pulses on then settles)
    shapes.append(ellipse("Ridge highlight", CX, 604, 150, 46,
                          fill=solid(C["cyan"], 0.55), soft=40,
                          fx=[fade_in(1.2, 0.5), fade_out(2.4, 0.8)]))
    shapes.append(poly("Ridge axis marker", [(CX, 540), (CX, 596)], closed=False,
                       ln=line(C["cyan"], 4, 1.0), fx=[fade_in(1.2, 0.5)]))
    # plate-motion arrows: appear at ridge flanks and glide outward
    yl = S.sf(150) - 34
    shapes.append(poly("Arrow left", arrow_pts(CX - 110, yl, CX - 290, yl, 16, 44, 40),
                       fill=solid(C["cyan"]), glow={"color": C["cyan"], "r": 10, "a": 0.45},
                       fx=[fade_in(1.8, 0.5), move(1.8, 1.6, -150, 0, 0.3, 0.5)]))
    shapes.append(poly("Arrow right", arrow_pts(CX + 110, yl, CX + 290, yl, 16, 44, 40),
                       fill=solid(C["cyan"]), glow={"color": C["cyan"], "r": 10, "a": 0.45},
                       fx=[fade_in(1.8, 0.5), move(1.8, 1.6, 150, 0, 0.3, 0.5)]))
    # titles
    shapes.append(text("Title", "Spreading Rates", 260, 92, 1400, 120, 66, bold=True,
                       fx=[fade_in(0.5, 0.7)]))
    shapes.append(text("Subtitle", "How Fast Is the Ocean Floor Moving?", 260, 226, 1400, 70, 32,
                       color="BFE9F2", fx=[fade_in(0.9, 0.7)]))
    shapes.append(text("Presenter name", "Edwin Wang", 560, 330, 800, 50, 24, bold=True,
                       fx=[fade_in(2.4, 0.6)]))
    shapes.append(text("Student number", "Student Number: [PLACEHOLDER]", 460, 378, 1000, 48, 22,
                       color=C["muted"], fx=[fade_in(2.6, 0.6)]))
    return dict(name="Opening", adv=5.0, transition=0.0, shapes=shapes,
                notes="Narration (0:00-0:05): \"Hi, I'm Edwin. Today, I'll explain seafloor spreading rates.\"")


# ================================================================ SLIDE 2
def slide2():
    G = 150
    S = Section(crest=600, k=5.0, ct=40, lk=7.0, gap=G)  # each plate moves 150 px; new crust fills 300 px
    T0, TD = 2.0, 3.6  # plate separation start / duration
    shapes = background()
    shapes.append(S.asthenosphere())
    # magma: partial-melt zone + axial magma lens, rising from below
    melt = poly("Melt zone (magma)", [(CX, 652), (CX + 230, 1080), (CX - 230, 1080)],
                fill=grad([(0, C["magma_hot"], 0.95), (0.35, C["magma"], 0.7), (1, C["magma"], 0.05)], 90),
                glow={"color": C["magma"], "r": 18, "a": 0.5})
    magma_grp = group("Rising magma", [melt], fx=[wipe_in(0.9, 1.3, "up")])
    shapes.append(magma_grp)
    # upward chevrons = magma ascending (each rises and fades)
    for i, (dx, y0, t0) in enumerate([(-60, 990, 1.4), (55, 960, 1.9), (0, 1010, 2.5), (-30, 985, 3.3), (40, 1000, 4.0)]):
        shapes.append(poly(f"Magma ascent {i+1}", chevron_up_pts(CX + dx * 0.6, y0),
                           fill=solid(C["magma_hot"]),
                           fx=[fade_in(t0, 0.3), move(t0, 1.4, -dx * 0.5, -230), fade_out(t0 + 1.0, 0.4)]))
    # new crust + new lithosphere: revealed from the axis outward, in step with the plates
    GX = G + 40
    # Hot upwelling mantle fills the space under the new crust.  It is coloured
    # exactly like the asthenosphere so that it reads as the same material.
    def asth_col(y):
        y_top, y_bot = S.crest + S.ct, H + 20
        f = (y - y_top) / (y_bot - y_top)
        a, b = int(C["asth_top"], 16), int(C["asth_bot"], 16)
        ch = [round(((a >> sh) & 255) * (1 - f) + ((b >> sh) & 255) * f) for sh in (16, 8, 0)]
        return "%02X%02X%02X" % tuple(ch)
    xs = S.xs(-GX, GX, 8)
    y_bot = S.lab(GX)
    upwell = poly("Upwelling mantle beneath new crust",
                  [(CX - GX, S.crest + S.ct), (CX + GX, S.crest + S.ct)] +
                  [(CX + x, S.lab(abs(x))) for x in xs[::-1]],
                  fill=grad([(0, asth_col(S.crest + S.ct), 1), (1, asth_col(y_bot), 1)], 90))
    new_crust = rect("New oceanic crust", CX - G, S.crest, 2 * G, S.ct,
                     fill=grad([(0, C["crust"], 1), (0.5, C["crust_new"], 1), (1, C["crust"], 1)], 0),
                     ln=line("C9D3DD", 1.5, 0.8))
    new_grp = group("New crust forming", [upwell, new_crust], fx=[split_out(T0, TD)])
    shapes.insert(shapes.index(magma_grp), new_grp)
    lens = ellipse("Axial magma lens", CX, S.crest + S.ct + 10, 46, 11,
                   fill=solid(C["magma_hot"]), glow={"color": C["magma"], "r": 14, "a": 0.7},
                   fx=[fade_in(1.9, 0.4)])
    shapes.append(lens)
    # the two plates (move apart; ridge axis stays put)
    yl = S.sf(150) - 34  # same place the slide-1 arrows finished, so the cross-fade is seamless
    L = S.plate("L", "Left plate") + [
        poly("Left plate arrow", arrow_pts(CX - 260, yl, CX - 440, yl, 16, 44, 40), fill=solid(C["cyan"]),
             glow={"color": C["cyan"], "r": 10, "a": 0.45})]
    R = S.plate("R", "Right plate") + [
        poly("Right plate arrow", arrow_pts(CX + 260, yl, CX + 440, yl, 16, 44, 40), fill=solid(C["cyan"]),
             glow={"color": C["cyan"], "r": 10, "a": 0.45})]
    shapes.append(group("Left plate", L, fx=[move(T0, TD, -G)]))
    shapes.append(group("Right plate", R, fx=[move(T0, TD, G)]))
    # ridge axis + labels
    shapes.append(poly("Ridge axis", [(CX, 418), (CX, 594)], closed=False,
                       ln=line(C["cyan_soft"], 3, 0.9, "dash"), fx=[fade_in(0.2, 0.5)]))
    shapes.append(text("Label: Mid-Ocean Ridge", "Mid-Ocean Ridge", 660, 350, 600, 60, 30, bold=True,
                       fx=[fade_in(0.2, 0.5)]))
    shapes.append(rect("Label bg: Magma", 1236, 842, 236, 68, r=12, fill=solid(C["pill"], 0.85),
                       fx=[fade_in(1.8, 0.5)]))
    shapes.append(poly("Leader: Magma", [(1236, 876), (1080, 876)], closed=False,
                       ln=line(C["magma_hot"], 3), fx=[fade_in(1.8, 0.5)]))
    shapes.append(text("Label: Magma", "Magma", 1236, 842, 236, 68, 30, bold=True,
                       color=C["magma_hot"], fx=[fade_in(1.8, 0.5)]))
    shapes.append(poly("Leader: New Oceanic Crust", [(1210, 492), (1050, 590)], closed=False,
                       ln=line(C["text"], 3), fx=[fade_in(4.9, 0.5)]))
    shapes.append(text("Label: New Oceanic Crust", "New Oceanic Crust", 1150, 430, 640, 60, 30, bold=True,
                       align="l", fx=[fade_in(4.9, 0.5)]))
    shapes.append(text("Citation", "(NOAA Ocean Exploration, no date; Parsons and Sclater, 1977)",
                       40, 28, 1100, 44, 18, color="C9D6E3", align="l", fx=[fade_in(0.2, 0.5)]))
    return dict(name="Seafloor spreading", adv=6.5, transition=0.5, shapes=shapes,
                notes="Narration (0:05-0:12): \"At mid-ocean ridges, plates separate, and rising magma forms new oceanic crust.\"")


# ================================================================ SLIDE 3
def slide3():
    S = Section(crest=660, k=3.4, ct=34, lk=6.0)
    shapes = background()
    shapes.append(S.asthenosphere())
    shapes += S.plate("L", "Left plate") + S.plate("R", "Right plate")
    # plate highlights (tint the crust of the flank being discussed)
    def flank_tint(side, s_in, s_out):
        sgn = -1 if side == "L" else 1
        xs = S.xs(CX, CX + sgn * 980)
        top = [(x, S.sf(abs(x - CX)) - 2) for x in xs]
        bot = [(x, S.sf(abs(x - CX)) + S.ct + 2) for x in xs]
        return poly(("Left" if side == "L" else "Right") + " flank highlight", top + bot[::-1],
                    fill=solid(C["cyan"], 0.45), fx=[fade_in(s_in, 0.4), fade_out(s_out, 0.5)])
    shapes.append(flank_tint("L", 0.5, 1.7))
    shapes.append(flank_tint("R", 1.5, 2.7))
    shapes.append(poly("Ridge axis", [(CX, 352), (CX, 656)], closed=False,
                       ln=line(C["cyan_soft"], 3, 0.8, "dash")))
    ya = 600
    xl, xr = 400, 1520
    shapes.append(poly("Half-rate arrow left", arrow_pts(CX - 8, ya, xl, ya, 18, 50, 46),
                       fill=solid(C["cyan"]), glow={"color": C["cyan"], "r": 10, "a": 0.5},
                       fx=[wipe_in(0.5, 0.9, "left")]))
    shapes.append(poly("Half-rate arrow right", arrow_pts(CX + 8, ya, xr, ya, 18, 50, 46),
                       fill=solid(C["cyan"]), glow={"color": C["cyan"], "r": 10, "a": 0.5},
                       fx=[wipe_in(1.5, 0.9, "right")]))
    for side, cx in (("left", (CX + xl) / 2), ("right", (CX + xr) / 2)):
        shapes.append(text(f"Label: Half-Spreading Rate ({side})", "Half-Spreading Rate", cx - 260, 396, 520, 50, 26,
                           bold=True, fx=[fade_in(2.5, 0.5)]))
        shapes.append(text(f"Label: 2 cm/yr ({side})", "2 cm/yr", cx - 200, 440, 400, 70, 40, bold=True,
                           color=C["cyan"], fx=[fade_in(2.5, 0.5)]))
        shapes.append(text(f"Caption: relative to ridge ({side})", "relative to ridge", cx - 200, 514, 400, 40, 20,
                           color=C["muted"], fx=[fade_in(2.5, 0.5)]))
    shapes.append(poly("Full-rate arrow", double_arrow_pts(xl, xr, 268, 18, 54, 48),
                       fill=solid("FFFFFF"), glow={"color": C["cyan"], "r": 12, "a": 0.55},
                       fx=[split_out(3.4, 1.0)]))
    shapes.append(text("Label: Full-Spreading Rate", "Full-Spreading Rate", 560, 74, 800, 60, 32, bold=True,
                       fx=[fade_in(4.0, 0.5)]))
    shapes.append(text("Label: 4 cm/yr", "4 cm/yr", 660, 134, 600, 84, 48, bold=True,
                       color="FFFFFF", fx=[fade_in(4.0, 0.5)]))
    shapes.append(text("Caption: plate separation", "relative plate separation", 560, 298, 800, 44, 20,
                       color=C["muted"], fx=[fade_in(4.0, 0.5)]))
    shapes.append(rect("Equation bg", 650, 880, 620, 100, r=50, fill=solid(C["pill"], 0.88),
                       ln=line(C["cyan"], 2, 0.8), fx=[fade_in(5.0, 0.5)]))
    shapes.append(text("Equation: 2 + 2 = 4 cm/yr", "2 + 2 = 4 cm/yr", 650, 880, 620, 100, 40, bold=True,
                       fx=[fade_in(5.0, 0.5)]))
    shapes.append(text("Caption: illustrative values", "Illustrative values (symmetric spreading)",
                       1000, 1004, 880, 48, 20, color="C9D6E3", align="r", fx=[fade_in(5.0, 0.5)]))
    shapes.append(text("Citation", "(Fowler, 2005; Müller et al., 2008)",
                       40, 1006, 700, 44, 18, color="C9D6E3", align="l", fx=[fade_in(5.0, 0.5)]))
    return dict(name="Half vs full spreading rate", adv=6.5, transition=0.5, shapes=shapes,
                notes="Narration (0:12-0:19): \"Each side's motion is a half-spreading rate. Together, they give the full separation rate.\"")


# ================================================================ SLIDE 4
def slide4():
    shapes = background()
    y0, h = 300, 400
    # oldest -> youngest; widths differ because reversal intervals are irregular
    widths = [100, 140, 70, 120, 100]
    pol = ["N", "R", "N", "R", "N"]  # youngest (at the ridge today) = normal polarity
    v = sum(widths) / 2.8  # px per second: constant spreading speed
    t_start = 0.6
    births = []
    t = t_start
    for w in widths:
        births.append((t, w / v))
        t += w / v
    t_end = t
    span = sum(widths)
    shapes.append(text("Label: Magnetic Stripes", "Magnetic Stripes", 460, 70, 1000, 80, 44, bold=True,
                       fx=[fade_in(0.1, 0.5), fade_out(4.4, 0.6)]))
    shapes.append(rect("Seafloor (map view)", CX - span - 30, y0, 2 * span + 60, h,
                       fill=solid(C["panel"]), ln=line("6F8BA8", 2, 0.8), r=8,
                       fx=[fade_out(4.4, 0.8)]))
    bands = []
    for i, (w, p) in enumerate(zip(widths, pol)):
        tb, db = births[i]
        later = sum(widths[i + 1:])
        col = C["normal"] if p == "N" else C["reversed"]
        tag = "normal" if p == "N" else "reversed"
        for side in ("L", "R"):
            sgn = -1 if side == "L" else 1
            x = CX - w if side == "L" else CX
            fx = [wipe_in(tb, db, "left" if side == "L" else "right")]
            if later:
                fx.append(move(tb + db, t_end - (tb + db), sgn * later))
            fx.append(fade_out(4.4, 0.8))
            bands.append(rect(f"Band {i+1} {tag} ({'left' if side == 'L' else 'right'})", x, y0, w, h,
                              fill=solid(col), fx=fx))
    shapes += bands
    # ridge axis (where new crust forms)
    shapes.append(poly("Ridge axis", [(CX, y0 - 24), (CX, y0 + h + 24)], closed=False,
                       ln=line(C["magma"], 6), glow=None, fx=[fade_out(4.4, 0.8)]))
    shapes.append(ellipse("Ridge axis glow", CX, y0 + h / 2, 22, h / 2 + 20,
                          fill=solid(C["magma"], 0.45), soft=18, fx=[fade_out(4.4, 0.8)]))
    shapes.append(text("Label: Mid-Ocean Ridge", "Mid-Ocean Ridge", 660, 212, 600, 56, 28, bold=True,
                       fx=[fade_in(0.1, 0.5), fade_out(4.4, 0.6)]))
    # matching-pattern highlight: the same wide reversed band on both flanks
    off = sum(widths[2:])
    for side in ("L", "R"):
        x = CX - off - widths[1] if side == "L" else CX + off
        shapes.append(rect(f"Match outline ({'left' if side == 'L' else 'right'})", x - 4, y0 - 12, widths[1] + 8, h + 24,
                           ln=line(C["cyan"], 5), r=6, glow={"color": C["cyan"], "r": 10, "a": 0.6},
                           fx=[fade_in(3.5, 0.4), fade_out(4.4, 0.6)]))
    # legend
    lx, ly = 500, 776
    shapes.append(rect("Legend swatch: normal", lx, ly, 56, 36, fill=solid(C["normal"]), ln=line("8FA6BE", 2),
                       fx=[fade_in(2.6, 0.5), fade_out(4.4, 0.6)]))
    shapes.append(text("Legend: Normal Polarity", "Normal Polarity", lx + 72, ly - 8, 380, 52, 24, align="l",
                       fx=[fade_in(2.6, 0.5), fade_out(4.4, 0.6)]))
    shapes.append(rect("Legend swatch: reversed", lx + 480, ly, 56, 36, fill=solid(C["reversed"]),
                       fx=[fade_in(2.6, 0.5), fade_out(4.4, 0.6)]))
    shapes.append(text("Legend: Reversed Polarity", "Reversed Polarity", lx + 552, ly - 8, 420, 52, 24, align="l",
                       fx=[fade_in(2.6, 0.5), fade_out(4.4, 0.6)]))
    # ---- simplification into the physical paper-strip model
    py0, ph = 380, 240
    paper = []
    for side in ("L", "R"):
        sgn = -1 if side == "L" else 1
        x0 = CX - span if side == "L" else CX
        paper.append(rect(f"Paper strip shadow ({side})", x0 + 10, py0 + 14, span, ph,
                          fill=solid("000000", 0.35), soft=10))
        paper.append(rect(f"Paper strip ({'left' if side == 'L' else 'right'})", x0, py0, span, ph,
                          fill=solid(C["paper"]), ln=line("C9C3B5", 1.5)))
        off = 0
        for w, p in zip(widths[::-1], pol[::-1]):  # youngest first, outward from ridge
            if p == "N":
                x = CX - off - w if side == "L" else CX + off
                paper.append(rect(f"Paper stripe ({side})", x, py0, w, ph, fill=solid(C["ink"])))
            off += w
    shapes.append(group("Paper strip model", paper, fx=[fade_in(4.5, 0.8)]))
    shapes.append(rect("Cardboard ridge shadow", CX - 26, py0 - 46, 70, ph + 100, fill=solid("000000", 0.35),
                       soft=10, fx=[fade_in(4.5, 0.8)]))
    shapes.append(rect("Cardboard ridge", CX - 34, py0 - 60, 68, ph + 120, r=6,
                       fill=grad([(0, "B99568", 1), (1, C["cardboard"], 1)], 0), ln=line(C["cardboard_dark"], 3),
                       fx=[fade_in(4.5, 0.8)]))
    shapes.append(text("Citation", "(Vine and Matthews, 1963; Kious and Tilling, 1996)",
                       460, 880, 1000, 44, 18, color="C9D6E3", fx=[fade_in(2.6, 0.5), fade_out(4.4, 0.6)]))
    return dict(name="Magnetic stripes", adv=5.5, transition=0.5, shapes=shapes,
                notes="Narration (0:19-0:25): \"Magnetic stripes record past field reversals. Here's how the pattern forms.\" "
                      "[CUT to camera: presenter holding the paper-strip model]")


# ================================================================ END CARD (references)
ACCESSED = "17 November 2026"
REFERENCES = [  # Harvard (Cite Them Right), as recommended by UCL Library; alphabetical
    [("Fowler, C.M.R. (2005) ", 0), ("The solid Earth: an introduction to global geophysics", 1),
     (". 2nd edn. Cambridge: Cambridge University Press.", 0)],
    [("Kious, W.J. and Tilling, R.I. (1996) ", 0), ("This dynamic Earth: the story of plate tectonics", 1),
     (". Reston, VA: U.S. Geological Survey. Available at: https://pubs.usgs.gov/gip/dynamic/dynamic.html (Accessed: %s)." % ACCESSED, 0)],
    [("Müller, R.D. et al. (2008) \u2018Age, spreading rates, and spreading asymmetry of the world\u2019s ocean crust\u2019, ", 0),
     ("Geochemistry, Geophysics, Geosystems", 1), (", 9(4), Q04006. Available at: https://doi.org/10.1029/2007GC001743.", 0)],
    [("NOAA Ocean Exploration (no date) ", 0), ("What is a mid-ocean ridge?", 1),
     (" Available at: https://oceanexplorer.noaa.gov/facts/mid-ocean-ridge.html (Accessed: %s)." % ACCESSED, 0)],
    [("Parsons, B. and Sclater, J.G. (1977) \u2018An analysis of the variation of ocean floor bathymetry and heat flow with age\u2019, ", 0),
     ("Journal of Geophysical Research", 1), (", 82(5), pp. 803\u2013827. Available at: https://doi.org/10.1029/JB082i005p00803.", 0)],
    [("Vine, F.J. and Matthews, D.H. (1963) \u2018Magnetic anomalies over oceanic ridges\u2019, ", 0), ("Nature", 1),
     (", 199(4897), pp. 947\u2013949. Available at: https://doi.org/10.1038/199947a0.", 0)],
]


def endcard():
    shapes = background()
    shapes.append(text("Heading: References", "References", 120, 60, 1680, 90, 40, bold=True, align="l",
                       fx=[fade_in(0.0, 0.5)]))
    shapes.append(rich("Reference list", REFERENCES, 120, 175, 1680, 19, color="E6EDF4",
                       fx=[fade_in(0.2, 0.6)]))
    shapes.append(text("Footer: style", "Referencing style: Harvard (Cite Them Right)",
                       120, 1000, 1680, 40, 16, color=C["muted"], align="l", fx=[fade_in(0.2, 0.6)]))
    return dict(name="References (end card)", adv=4.0, transition=0.0, shapes=shapes, hidden=True,
                notes="End card: place after the on-camera demonstration (after 1:00 of content). "
                      "This slide is HIDDEN so the 25-second Part 1 export is unaffected; "
                      "a ready-made clip is supplied as Spreading_Rates_References_EndCard.mp4.")


def build():
    slides = [slide1(), slide2(), slide3(), slide4()]
    t = 0.0
    for s in slides:
        s["t0"] = t
        t += s["transition"] + s["adv"]
        # sanity: every effect finishes before the slide advances
        def walk(shs):
            for sh in shs:
                for e in sh["fx"]:
                    assert e["s"] + e["d"] <= s["adv"] + 1e-6, (s["name"], sh["name"], e)
                if sh["kind"] == "group":
                    walk(sh["children"])
        walk(s["shapes"])
    ec = endcard()
    assert ec["shapes"][-2]["y"] + ec["shapes"][-2]["h"] < 990, "reference list too long"
    return dict(W=W, H=H, fps=30, total=t, font=FONT, slides=slides, endcard=ec)


if __name__ == "__main__":
    scene = build()
    out = os.path.join(os.path.dirname(__file__), "scene.json")
    with open(out, "w") as f:
        json.dump(scene, f, indent=1)
    print("total", scene["total"], "s ->", out)
