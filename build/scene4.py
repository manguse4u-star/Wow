"""v8: v6 visual template, re-timed to the new narration (hook -> question -> demo -> payoff).

New intro lines (Chinese voice, English subtitles), planned timing in seconds:
  L1 0.4-4.0   Hi, I'm Edwin, student number 25092450.
  L2 4.4-8.9   The Atlantic widens by about 2-3 cm a year - about as fast as fingernails grow.
  L3 9.3-12.0  That's because the plates either side of the mid-ocean ridge are moving apart.
  L4 12.2-17.0 One side's speed is the half-spreading rate; both together, the full rate.
  L5 17.5-22.5 But no one can watch a plate for millions of years - so how do we measure it?
Closing lines:
  C1 0.5-5.6   So the seafloor is like a tape recorder, logging every flip of Earth's field.
  C2 6.0-10.6  Read the stripes, and we can measure motion slower than fingernails grow.
"""
import json
import math
import os

import scene2 as V2
from scene import (W, H, CX, poly, rect, ellipse, group, solid, grad, line, fade_in, fade_out,
                   wipe_in, split_out, move, arrow_pts, double_arrow_pts, Section)
from scene2 import (T, textured, leader, label, tag, streaks, mantle_col, plate, BG, MUTED, CYAN, LIME, ORANGE,
                    background, cross_section)

INTRO_LINES = [
    (0.4, 4.0, "大家好，我是 Edwin，学号 25092450。", "Hi, I'm Edwin, student number 25092450."),
    (4.4, 8.9, "大西洋每年会变宽两三厘米，跟指甲长得差不多快。", "The Atlantic widens by about 2–3 cm a year — about as fast as your fingernails grow."),
    (9.3, 12.0, "因为洋中脊两侧的板块正在分开：", "That's because the plates on either side of the mid-ocean ridge are moving apart."),
    (12.2, 17.0, "一侧的速度是半扩张速率，两侧加起来是全扩张速率。", "One side's speed is the half-spreading rate; both sides together give the full-spreading rate."),
    (17.5, 22.5, "可没人能盯着板块看几百万年，那速度是怎么测出来的？", "But no one can watch a plate for millions of years — so how do we measure its speed?"),
]
CLOSING_LINES = [
    (0.5, 5.6, "所以，海底就像一盘磁带，录下了地磁场的每一次翻转。", "So the seafloor works like a tape recorder, logging every flip of Earth's magnetic field."),
    (6.0, 10.6, "读懂这些条带，就能测出比指甲生长还慢的速度。", "Read the stripes, and we can measure motion slower than your fingernails grow."),
]
INTRO_LEN, CLOSING_LEN, XF = 23.0, 13.7, 0.5


# ------------------------------------------------------------------ Atlantic map (hook)
SAM = [(-330, -300), (-250, -330), (-150, -310), (-80, -260), (-20, -200), (-40, -130), (-10, -60), (-40, 20),
       (-90, 100), (-130, 170), (-170, 240), (-200, 300), (-230, 330), (-250, 280), (-260, 200), (-300, 120),
       (-340, 40), (-370, -60), (-380, -160), (-360, -240)]
AFR = [(60, -330), (160, -340), (260, -320), (330, -290), (360, -230), (330, -170), (300, -110), (310, -40),
       (300, 40), (270, 120), (240, 190), (200, 260), (160, 300), (120, 270), (100, 200), (90, 120),
       (60, 60), (20, 10), (10, -60), (20, -150), (40, -240)]


def slide_atlantic(dur):
    sh = background()
    cx, cy, sc = CX, 560, 1.15
    tr = lambda pts, dx=0: [(cx + (x + dx) * sc, cy + y * sc) for x, y in pts]
    ocean = rect("Ocean", 0, 0, W, H, fill=grad([(0, "0B2440", 1), (1, "0F3456", 1)], 90))
    sh.append(group("Ocean", [ocean], fx=[fade_in(0.0, 0.5)]))
    ridge = [(cx + 8 * math.sin(i * 1.3) * sc + (6 if i % 2 else -6), cy + (-360 + i * 30) * sc) for i in range(25)]
    sh.append(poly("Mid-Atlantic Ridge", ridge, closed=False, ln=line(ORANGE, 5), glow={"color": ORANGE, "r": 10, "a": 0.6},
                   fx=[fade_in(0.3, 0.6)]))
    land_fx = lambda sgn: [fade_in(0.2, 0.6), move(0.2, dur - 0.2, sgn * 26, 0)]
    sh.append(textured("South America", tr(SAM), "3E5A48", "22352A", 34, 51, vary=0.10))
    sh[-1]["fx"] = land_fx(-1)
    sh.append(textured("Africa", tr(AFR), "5B5440", "352F22", 34, 53, vary=0.10))
    sh[-1]["fx"] = land_fx(1)
    sh.append(poly("Arrow W", arrow_pts(cx - 60, cy - 40, cx - 230, cy - 40, 12, 38, 34), fill=solid(CYAN), fx=[wipe_in(1.4, 0.6, "left")]))
    sh.append(poly("Arrow E", arrow_pts(cx + 60, cy - 40, cx + 230, cy - 40, 12, 38, 34), fill=solid(CYAN), fx=[wipe_in(1.4, 0.6, "right")]))
    sh.append(label("Atlantic label", "Atlantic Ocean", "widening ≈ 2–3 cm per year", 1420, 300, fx=[fade_in(1.0, 0.5)]))
    sh.append(label("Nail label", "≈ fingernail growth", "a few cm per year", 1420, 470, term_color=CYAN, fx=[fade_in(2.6, 0.5)]))
    sh.append(label("Ridge label", "Mid-Atlantic Ridge", "", 140, 840, term_color="FFC48A", fx=[fade_in(0.8, 0.5)]))
    sh.append(leader("Ridge leader", 470, 865, cx - 4, cy + 300 * sc - 30, color="FFC48A", fx=[fade_in(0.8, 0.5)]))
    sh.append(tag("Map · schematic, not to scale", fx=[fade_in(0.3, 0.5)]))
    sh.append(T("Citation", "(Kious and Tilling, 1996)", 1400, 36, 460, 40, 22, align="r", color="9AA6B5", fx=[fade_in(1.0, 0.5)]))
    return dict(name="Atlantic widening", adv=dur, transition=0, shapes=sh)


# ------------------------------------------------------------------ cross-section with re-timed rates
def slide_section(dur, rate_t=3.0):
    G = 150
    S = Section(crest=610, k=5.0, ct=40, lk=7.0, gap=G)
    sh = cross_section("X", S, G)
    T0, TD = 0.5, 3.4
    GX = G + 40
    xs = S.xs(-GX, GX, 8)
    up = poly("Upwelling mantle", [(CX - GX, S.crest + S.ct), (CX + GX, S.crest + S.ct)] + [(CX + x, S.lab(abs(x))) for x in xs[::-1]],
              fill=grad([(0, mantle_col(S, S.crest + S.ct), 1), (1, mantle_col(S, S.lab(GX)), 1)], 90))
    nc = textured("New oceanic crust", [(CX - G, S.crest), (CX + G, S.crest), (CX + G, S.crest + S.ct), (CX - G, S.crest + S.ct)],
                  "8794A6", "3A4350", 22, 41, vary=0.08)
    ncl = poly("New crust top", [(CX - G, S.crest), (CX + G, S.crest)], closed=False, ln=line("E8EEF5", 2.5, 0.9))
    sh.insert(-1, group("New crust forming", [up, nc, ncl], fx=[split_out(T0, TD)]))
    sh.append(ellipse("Axial magma", CX, S.crest + S.ct + 10, 44, 10, fill=solid("FFD08A"), glow={"color": ORANGE, "r": 14, "a": 0.7},
                      fx=[fade_in(0.6, 0.4)]))
    sh.append(group("Left plate", plate(S, "L", 3), fx=[move(T0, TD, -G)]))
    sh.append(group("Right plate", plate(S, "R", 5), fx=[move(T0, TD, G)]))
    sh.append(tag("Schematic · not to scale", fx=[fade_in(0.2, 0.5)]))
    out = [fade_out(rate_t - 0.3, 0.3)]
    sh.append(label("Ridge label", "Mid-ocean ridge", "where plates separate", CX, 262, align="ctr", fx=[fade_in(0.2, 0.5)] + out))
    sh.append(leader("Ridge leader", CX, 360, CX, S.crest - 8, fx=[fade_in(0.3, 0.5)] + out))
    sh.append(label("Plate label", "Oceanic plate", "moves away from the ridge", 150, 330, fx=[fade_in(0.9, 0.5)] + out))
    sh.append(leader("Plate leader", 300, 420, 470, S.sf(490) - 6, fx=[fade_in(0.9, 0.5)] + out))
    ya, xl, xr = 520, 560, 1360
    r = rate_t
    sh.append(poly("Half arrow left", arrow_pts(CX - 6, ya, xl, ya, 14, 44, 40), fill=solid(CYAN), fx=[wipe_in(r, 0.6, "left")]))
    sh.append(poly("Half arrow right", arrow_pts(CX + 6, ya, xr, ya, 14, 44, 40), fill=solid(CYAN), fx=[wipe_in(r + 0.3, 0.6, "right")]))
    sh.append(label("Half label", "Half-spreading rate", "one plate, relative to the ridge", 150, 430, term_color=CYAN, fx=[fade_in(r, 0.5)]))
    sh.append(T("Half value L", "2 cm/yr", CX - 400, 548, 390, 50, 36, color=CYAN, weight=600, align="ctr", fx=[fade_in(r + 0.6, 0.4)]))
    sh.append(T("Half value R", "2 cm/yr", CX + 10, 548, 390, 50, 36, color=CYAN, weight=600, align="ctr", fx=[fade_in(r + 0.8, 0.4)]))
    sh.append(poly("Full arrow", double_arrow_pts(xl, xr, 300, 12, 44, 40), fill=solid(LIME), fx=[split_out(r + 1.9, 0.7)]))
    sh.append(label("Full label", "Full-spreading rate", "separation of the two plates", CX, 160, align="ctr", term_color=LIME, w=800,
                    fx=[fade_in(r + 2.0, 0.5)]))
    sh.append(T("Full value", "4 cm/yr", CX - 200, 320, 400, 50, 36, color=LIME, weight=600, align="ctr", fx=[fade_in(r + 2.5, 0.4)]))
    sh.append(T("Symmetric note", "symmetric example: 2 + 2 = 4", 1300, 40, 560, 44, 24, color="C9D1DB", align="r", fx=[fade_in(r + 2.8, 0.5)]))
    return dict(name="Spreading rate", adv=dur, transition=0, shapes=sh)


# ------------------------------------------------------------------ the question
def slide_question(dur):
    sh = background()
    # a single plate drifting very slowly with a "millions of years" time bar
    S = Section(crest=760, k=3.0, ct=34, lk=5.0)
    xs = S.xs(-20, W + 20, 8)
    top = [(x, S.asth_top(abs(x - CX))) for x in xs]
    asth = poly("Asthenosphere", top + [(W + 20, H + 20), (-20, H + 20)], fill=grad([(0, "B3612A", 1), (1, "5C2812", 1)], 90))
    sh.append(group("Section", [asth], fx=[fade_in(0.0, 0.5)]))
    sh.append(group("Left plate", plate(S, "L", 7), fx=[fade_in(0.0, 0.5), move(0.0, dur, -10, 0)]))
    sh.append(group("Right plate", plate(S, "R", 8), fx=[fade_in(0.0, 0.5), move(0.0, dur, 10, 0)]))
    sh.append(rect("Time bar bg", 460, 360, 1000, 10, r=5, fill=solid("FFFFFF", 0.12), fx=[fade_in(0.2, 0.4)]))
    sh.append(rect("Time bar", 460, 360, 1000, 10, r=5, fill=solid(CYAN), fx=[wipe_in(0.4, dur - 1.2, "right")]))
    sh.append(T("Time 0", "now", 460, 300, 300, 50, 30, color=MUTED, fx=[fade_in(0.2, 0.4)]))
    sh.append(T("Time end", "millions of years", 1060, 300, 400, 50, 30, color=MUTED, align="r", fx=[fade_in(0.2, 0.4)]))
    sh.append(T("Question mark", "?", CX - 100, 440, 200, 200, 150, weight=700, color=INK_Q, align="ctr", fx=[fade_in(2.6, 0.6)]))
    return dict(name="Question", adv=dur, transition=0, shapes=sh)


INK_Q = "F2F4F7"


# ------------------------------------------------------------------ closing: tape recorder -> paper model
def slide_tape(dur=11.0):
    sl = V2.slide_stripes(dur, form=True, paper=True)
    # retime: formation as in v2 (0.5-3.3 s), model morph later (6.0 s)
    for shp in sl["shapes"]:
        new = []
        for e in shp["fx"]:
            e = dict(e)
            if e["type"] == "fade_out" and abs(e["s"] - 4.0) < 1e-6:
                e["s"] = 5.6
            if e["type"] == "fade_in" and abs(e["s"] - 4.1) < 1e-6:
                e["s"] = 5.8
            if e["type"] == "fade_in" and abs(e["s"] - 4.5) < 1e-6:
                e["s"] = 6.4
            new.append(e)
        shp["fx"] = new
        if shp["name"] == "Model label":
            shp["children"][0]["text"] = "Read the stripes"
            shp["children"][1]["text"] = "distance ÷ age = spreading rate"
    sl["shapes"].append(label("Tape label", "Seafloor = tape recorder", "every magnetic flip is recorded", CX, 875, align="ctr",
                              w=900, term_color="FFC48A", fx=[fade_in(1.0, 0.5), fade_out(5.4, 0.4)]))
    sl["shapes"].append(T("Citation", "(Vine and Matthews, 1963)", 1400, 36, 460, 40, 22, align="r", color="9AA6B5", fx=[fade_in(1.0, 0.5)]))
    # the original legend overlaps the new label position -> move legend up a bit
    for shp in sl["shapes"]:
        if shp["name"].startswith("Legend"):
            for k in ("y",):
                shp[k] = shp[k] - 0
    sl["name"] = "Tape recorder"
    return sl


def build():
    slides = [V2.slide_title(), slide_atlantic(5.4), slide_section(9.1, rate_t=3.0), slide_question(6.0),
              slide_tape(11.0), V2.slide_refs()]
    for s in slides:
        if s["name"] == "Title":
            s["adv"] = 4.9
    seqs = {
        # title 0-4.9 | Atlantic 4.4-9.8 | section 9.3-18.4 | question 17.9-23.9 -> 23.0 total
        "v8_intro": {"xf": XF, "segments": [{"slide": 0, "dur": 4.9}, {"slide": 1, "dur": 5.4}, {"slide": 2, "dur": 9.1},
                                             {"slide": 3, "dur": 5.1}]},
        "v8_closing": {"xf": XF, "segments": [{"slide": 4, "dur": 11.0}, {"slide": 5, "dur": 3.2}]},
    }
    return dict(W=W, H=H, fps=30, total=0, font="Inter", font_css=V2.FONT_CSS, slides=slides, sequences=seqs)


if __name__ == "__main__":
    sc = build()
    json.dump(sc, open(os.path.join(os.path.dirname(__file__), "scene4.json"), "w"))
    for k, v in sc["sequences"].items():
        print(k, round(sum(s["dur"] for s in v["segments"]) - v["xf"] * (len(v["segments"]) - 1), 2))
