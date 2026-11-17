"""Build Spreading_Rates_Animated.pptx from scene.json.

Every visual is a native, editable PowerPoint shape (freeforms, rectangles,
ovals, text boxes, groups).  Every animation is written as native PowerPoint
OOXML timing (Fade, Wipe, Split, Motion Path, Fade-exit), all set to run
automatically ("With Previous" + delay), and every slide auto-advances.
"""
import json
import os
import sys

from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

EMU = 6350  # per px
HERE = os.path.dirname(os.path.abspath(__file__))
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def E(px):
    return Emu(int(round(px * EMU)))


def el(tag, **attrs):
    ns, name = tag.split(":")
    e = etree.Element("{%s}%s" % (A if ns == "a" else P, name))
    for k, v in attrs.items():
        e.set(k, str(v))
    return e


def color_el(hexc, alpha=1.0):
    c = el("a:srgbClr", val=hexc)
    if alpha < 0.999:
        c.append(el("a:alpha", val=int(round(alpha * 100000))))
    return c


def fill_el(f):
    if f is None:
        return el("a:noFill")
    if f["type"] == "solid":
        s = el("a:solidFill")
        s.append(color_el(f["color"], f.get("a", 1)))
        return s
    g = el("a:gradFill", rotWithShape="1")
    gs = el("a:gsLst")
    for pos, col, a in f["stops"]:
        st = el("a:gs", pos=int(round(pos * 100000)))
        st.append(color_el(col, a))
        gs.append(st)
    g.append(gs)
    g.append(el("a:lin", ang=int(f["angle"] * 60000), scaled="0"))
    return g


def line_el(ln):
    if ln is None:
        l = el("a:ln")
        l.append(el("a:noFill"))
        return l
    l = el("a:ln", w=int(ln["w"] * EMU), cap="rnd")
    s = el("a:solidFill")
    s.append(color_el(ln["color"], ln.get("a", 1)))
    l.append(s)
    if ln.get("dash"):
        l.append(el("a:prstDash", val=ln["dash"]))
    l.append(el("a:round"))
    return l


def style_shape(shape, d):
    sp = shape._element
    spPr = sp.find(qn("p:spPr"))
    for tag in ("a:noFill", "a:solidFill", "a:gradFill", "a:ln", "a:effectLst"):
        for x in spPr.findall(qn(tag)):
            spPr.remove(x)
    spPr.append(fill_el(d.get("fill")))
    spPr.append(line_el(d.get("line")))
    if d.get("glow") or d.get("soft"):
        fx = el("a:effectLst")
        if d.get("glow"):
            g = el("a:glow", rad=int(d["glow"]["r"] * EMU))
            g.append(color_el(d["glow"]["color"], d["glow"]["a"]))
            fx.append(g)
        if d.get("soft"):
            fx.append(el("a:softEdge", rad=int(d["soft"] * EMU)))
        spPr.append(fx)
    st = sp.find(qn("p:style"))
    if st is not None:
        sp.remove(st)


def add_shape(shapes, d):
    k = d["kind"]
    if k == "group":
        g = shapes.add_group_shape()
        for c in d["children"]:
            assert not c["fx"], "animations only on top-level shapes"
            add_shape(g.shapes, c)
        g.name = d["name"]
        return g
    if k == "poly":
        pts = d["pts"]
        b = shapes.build_freeform(pts[0][0], pts[0][1], scale=float(EMU))
        b.add_line_segments([tuple(p) for p in pts[1:]], close=d["closed"])
        s = b.convert_to_shape()
        style_shape(s, d)
    elif k in ("rect", "ellipse"):
        if k == "ellipse":
            kind = MSO_SHAPE.OVAL
        else:
            kind = MSO_SHAPE.ROUNDED_RECTANGLE if d.get("r") else MSO_SHAPE.RECTANGLE
        s = shapes.add_shape(kind, E(d["x"]), E(d["y"]), E(d["w"]), E(d["h"]))
        if k == "rect" and d.get("r"):
            s.adjustments[0] = min(0.5, d["r"] / min(d["w"], d["h"]))
        style_shape(s, d)
        if s.has_text_frame:
            s.text_frame.text = ""
    elif k == "text":
        s = shapes.add_textbox(E(d["x"]), E(d["y"]), E(d["w"]), E(d["h"]))
        tf = s.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = {"ctr": PP_ALIGN.CENTER, "l": PP_ALIGN.LEFT, "r": PP_ALIGN.RIGHT}[d["align"]]
        r = p.add_run()
        r.text = d["text"]
        r.font.name = FONT
        r.font.size = Pt(d["size"])
        r.font.bold = d["bold"]
        r.font.color.rgb = RGBColor.from_string(d["color"])
    elif k == "rich":
        s = shapes.add_textbox(E(d["x"]), E(d["y"]), E(d["w"]), E(d["h"]))
        tf = s.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = MSO_ANCHOR.TOP
        for i, para in enumerate(d["paras"]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = PP_ALIGN.LEFT
            p.line_spacing = Pt(d["size"] * d["line"])
            p.space_after = Pt(d["size"] * d["gap"])
            for t, it in para["runs"]:
                r = p.add_run()
                r.text = t
                r.font.name = FONT
                r.font.size = Pt(d["size"])
                r.font.italic = bool(it)
                r.font.color.rgb = RGBColor.from_string(d["color"])
    else:
        raise ValueError(k)
    s.name = d["name"]
    return s


# ---------------------------------------------------------------- animation timing
class Timing:
    def __init__(self):
        self.nid = 0

    def id(self):
        self.nid += 1
        return self.nid

    def bhvr(self, spid, dur, attrs=None, delay=None):
        c = el("p:cBhvr")
        ctn = el("p:cTn", id=self.id(), dur=dur)
        if delay is not None:
            ctn.set("fill", "hold")
            sc = el("p:stCondLst")
            sc.append(el("p:cond", delay=delay))
            ctn.append(sc)
        elif attrs and "ppt_x" in attrs:
            ctn.set("fill", "hold")
        c.append(ctn)
        t = el("p:tgtEl")
        t.append(el("p:spTgt", spid=spid))
        c.append(t)
        if attrs:
            al = el("p:attrNameLst")
            for a in attrs:
                an = el("p:attrName")
                an.text = a
                al.append(an)
            c.append(al)
        return c

    def set_vis(self, spid, val, delay=0):
        s = el("p:set")
        s.append(self.bhvr(spid, 1, ["style.visibility"], delay=delay))
        to = el("p:to")
        to.append(el("p:strVal", val=val))
        s.append(to)
        return s

    def effect(self, spid, e, node_type):
        ms = lambda sec: int(round(sec * 1000))
        typ = e["type"]
        if typ in ("fade_in", "wipe_in", "split_out"):
            pid, cls, sub, flt = {
                "fade_in": (10, "entr", 0, "fade"),
                "wipe_in": (22, "entr", {"up": 4, "down": 1, "left": 2, "right": 8}.get(e.get("dir"), 4),
                            "wipe(%s)" % e.get("dir")),
                "split_out": (16, "entr", 42, "barn(outVertical)"),
            }[typ]
        elif typ == "fade_out":
            pid, cls, sub, flt = 10, "exit", 0, "fade"
        elif typ == "move":
            pid, cls, sub, flt = 0, "path", 0, None
        par = el("p:par")
        ctn = el("p:cTn", id=self.id(), presetID=pid, presetClass=cls, presetSubtype=sub,
                 fill="hold", nodeType=node_type)
        if typ == "move":
            if e.get("accel"):
                ctn.set("accel", str(int(e["accel"] * 100000)))
            if e.get("decel"):
                ctn.set("decel", str(int(e["decel"] * 100000)))
        sc = el("p:stCondLst")
        sc.append(el("p:cond", delay=ms(e["s"])))
        ctn.append(sc)
        kids = el("p:childTnLst")
        d = ms(e["d"])
        if cls == "entr":
            kids.append(self.set_vis(spid, "visible"))
            ae = el("p:animEffect", transition="in", filter=flt)
            ae.append(self.bhvr(spid, d))
            kids.append(ae)
        elif cls == "exit":
            ae = el("p:animEffect", transition="out", filter=flt)
            ae.append(self.bhvr(spid, d))
            kids.append(ae)
            kids.append(self.set_vis(spid, "hidden", delay=d - 1))
        else:
            path = "M 0 0 L %.6f %.6f E" % (e["dx"] / 1920.0, e["dy"] / 1080.0)
            am = el("p:animMotion", origin="layout", path=path, pathEditMode="relative",
                    rAng="0", ptsTypes="AA")
            am.append(self.bhvr(spid, d, ["ppt_x", "ppt_y"]))
            am.append(el("p:rCtr", x=0, y=0))
            kids.append(am)
        ctn.append(kids)
        par.append(ctn)
        return par

    def build(self, items):
        """items: list of (spid, effect)."""
        timing = el("p:timing")
        tnl = el("p:tnLst")
        timing.append(tnl)
        root_par = el("p:par")
        tnl.append(root_par)
        root = el("p:cTn", id=self.id(), dur="indefinite", restart="never", nodeType="tmRoot")
        root_par.append(root)
        rk = el("p:childTnLst")
        root.append(rk)
        seq = el("p:seq", concurrent="1", nextAc="seek")
        rk.append(seq)
        main_id = self.id()
        main = el("p:cTn", id=main_id, dur="indefinite", nodeType="mainSeq")
        seq.append(main)
        mk = el("p:childTnLst")
        main.append(mk)
        click = el("p:par")
        mk.append(click)
        cctn = el("p:cTn", id=self.id(), fill="hold")
        click.append(cctn)
        sc = el("p:stCondLst")
        sc.append(el("p:cond", delay="indefinite"))
        ob = el("p:cond", evt="onBegin", delay="0")
        ob.append(el("p:tn", val=main_id))
        sc.append(ob)
        cctn.append(sc)
        ck = el("p:childTnLst")
        cctn.append(ck)
        inner = el("p:par")
        ck.append(inner)
        ictn = el("p:cTn", id=self.id(), fill="hold")
        inner.append(ictn)
        isc = el("p:stCondLst")
        isc.append(el("p:cond", delay="0"))
        ictn.append(isc)
        ik = el("p:childTnLst")
        ictn.append(ik)
        items = sorted(items, key=lambda it: it[1]["s"])
        for i, (spid, e) in enumerate(items):
            ik.append(self.effect(spid, e, "afterEffect" if i == 0 else "withEffect"))
        prev = el("p:prevCondLst")
        c = el("p:cond", evt="onPrev", delay="0")
        t = el("p:tgtEl"); t.append(el("p:sldTgt")); c.append(t); prev.append(c)
        nxt = el("p:nextCondLst")
        c = el("p:cond", evt="onNext", delay="0")
        t = el("p:tgtEl"); t.append(el("p:sldTgt")); c.append(t); nxt.append(c)
        seq.append(prev)
        seq.append(nxt)
        return timing


def main(out):
    global FONT
    scene = json.load(open(os.path.join(HERE, "scene.json")))
    FONT = scene["font"]
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    prs.core_properties.title = "Spreading Rates - How Fast Is the Ocean Floor Moving?"
    prs.core_properties.author = "Edwin Wang"
    blank = prs.slide_layouts[6]
    for sd in scene["slides"] + [scene["endcard"]]:
        slide = prs.slides.add_slide(blank)
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = RGBColor.from_string("071A33")
        items = []
        for d in sd["shapes"]:
            s = add_shape(slide.shapes, d)
            for e in d["fx"]:
                items.append((s.shape_id, e))
        sld = slide._element
        clr = sld.find(qn("p:clrMapOvr"))
        anchor = clr if clr is not None else sld.find(qn("p:cSld"))
        tr = el("p:transition", advTm=int(round(sd["adv"] * 1000)))
        if sd["transition"] > 0:
            tr.set("spd", "fast")  # 0.5 s
            tr.append(el("p:fade"))
        anchor.addnext(tr)
        if items:
            tr.addnext(Timing().build(items))
        slide.notes_slide.notes_text_frame.text = sd["notes"]
        if sd.get("hidden"):
            sld.set("show", "0")  # hidden: skipped by slide show / video export of Part 1
    prs.save(out)
    print("saved", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "deliverables", "Spreading_Rates_Animated.pptx"))
