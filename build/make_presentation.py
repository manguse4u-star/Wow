"""Build Spreading_Rates_Presentation.pptx - the deck used for recording.

  1  Title + name + student number (native animation, you introduce yourself)
  2  Embedded animation clip (auto-plays; starts straight at seafloor spreading)
     -> in the edit, cut to the on-camera paper-strip demonstration here
  3  Key-concepts recap: three diagrams + one relation (cards fade in)
  4  Embedded references end card (auto-plays)
"""
import json
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu

import make_pptx as M
from scene import C, build, rect, text, fade_in

HERE = os.path.dirname(os.path.abspath(__file__))
DEL = os.path.join(HERE, "..", "deliverables")
M.FONT = "Arial"


def autoplay_timing(spid, dur_ms):
    """'Start: Automatically' media timing, as PowerPoint writes it."""
    T = M.Timing()
    timing = M.el("p:timing")
    tnl = M.el("p:tnLst"); timing.append(tnl)
    par = M.el("p:par"); tnl.append(par)
    root = M.el("p:cTn", id=T.id(), dur="indefinite", restart="never", nodeType="tmRoot"); par.append(root)
    rk = M.el("p:childTnLst"); root.append(rk)
    seq = M.el("p:seq", concurrent="1", nextAc="seek"); rk.append(seq)
    main_id = T.id()
    main = M.el("p:cTn", id=main_id, dur="indefinite", nodeType="mainSeq"); seq.append(main)
    mk = M.el("p:childTnLst"); main.append(mk)
    p1 = M.el("p:par"); mk.append(p1)
    c1 = M.el("p:cTn", id=T.id(), fill="hold"); p1.append(c1)
    sc = M.el("p:stCondLst"); c1.append(sc)
    sc.append(M.el("p:cond", delay="indefinite"))
    ob = M.el("p:cond", evt="onBegin", delay="0"); ob.append(M.el("p:tn", val=main_id)); sc.append(ob)
    k1 = M.el("p:childTnLst"); c1.append(k1)
    p2 = M.el("p:par"); k1.append(p2)
    c2 = M.el("p:cTn", id=T.id(), fill="hold"); p2.append(c2)
    s2 = M.el("p:stCondLst"); s2.append(M.el("p:cond", delay="0")); c2.append(s2)
    k2 = M.el("p:childTnLst"); c2.append(k2)
    p3 = M.el("p:par"); k2.append(p3)
    c3 = M.el("p:cTn", id=T.id(), presetID="1", presetClass="mediacall", presetSubtype="0",
              fill="hold", nodeType="afterEffect"); p3.append(c3)
    s3 = M.el("p:stCondLst"); s3.append(M.el("p:cond", delay="0")); c3.append(s3)
    k3 = M.el("p:childTnLst"); c3.append(k3)
    cmd = M.el("p:cmd", type="call", cmd="playFrom(0.0)"); k3.append(cmd)
    cb = M.el("p:cBhvr"); cmd.append(cb)
    cb.append(M.el("p:cTn", id=T.id(), dur=dur_ms, fill="hold"))
    tg = M.el("p:tgtEl"); tg.append(M.el("p:spTgt", spid=spid)); cb.append(tg)
    for evt, tag in (("onPrev", "p:prevCondLst"), ("onNext", "p:nextCondLst")):
        lst = M.el(tag); c = M.el("p:cond", evt=evt, delay="0")
        t = M.el("p:tgtEl"); t.append(M.el("p:sldTgt")); c.append(t); lst.append(c); seq.append(lst)
    vid = M.el("p:video"); rk.append(vid)
    cm = M.el("p:cMediaNode", vol="80000"); vid.append(cm)
    ct = M.el("p:cTn", id=T.id(), fill="hold", display="0"); cm.append(ct)
    s4 = M.el("p:stCondLst"); s4.append(M.el("p:cond", delay="indefinite")); ct.append(s4)
    tg = M.el("p:tgtEl"); tg.append(M.el("p:spTgt", spid=spid)); cm.append(tg)
    return timing


def set_transition(slide, fade=True, adv_ms=None):
    sld = slide._element
    for old in sld.findall(M.qn("p:transition")):
        sld.remove(old)
    tr = M.el("p:transition")
    if fade:
        tr.set("spd", "fast")
        tr.append(M.el("p:fade"))
    if adv_ms:
        tr.set("advTm", str(adv_ms))
    sld.find(M.qn("p:clrMapOvr")).addnext(tr)
    return tr


def put_timing(slide, timing):
    sld = slide._element
    for old in sld.findall(M.qn("p:timing")):
        sld.remove(old)
    anchor = sld.find(M.qn("p:transition"))
    if anchor is None:
        anchor = sld.find(M.qn("p:clrMapOvr"))
    anchor.addnext(timing)


def video_slide(prs, mp4, poster, dur_s, notes):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string("071A33")
    mv = slide.shapes.add_movie(mp4, 0, 0, prs.slide_width, prs.slide_height,
                                poster_frame_image=poster, mime_type="video/mp4")
    mv.name = os.path.basename(mp4)
    set_transition(slide, fade=True)
    put_timing(slide, autoplay_timing(mv.shape_id, int(round(dur_s * 1000))))
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def crop(src, box, out, size):
    im = Image.open(src)
    k = im.width / 1920
    im = im.crop(tuple(int(v * k) for v in box)).resize(size, Image.LANCZOS)
    im.save(out)
    return out


def main():
    scene = build()
    clip = json.load(open(os.path.join(HERE, "clip.json")))
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    prs.core_properties.title = "Spreading Rates - How Fast Is the Ocean Floor Moving?"
    prs.core_properties.author = "Edwin Wang"

    # 1 -- title, name, student number (same design and animation as before)
    s1 = scene["slides"][0]
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string("071A33")
    items = []
    for d in s1["shapes"]:
        sh = M.add_shape(slide.shapes, d)
        items += [(sh.shape_id, e) for e in d["fx"]]
    set_transition(slide, fade=False)
    put_timing(slide, M.Timing().build(items))
    slide.notes_slide.notes_text_frame.text = (
        "YOU (voice or on camera): \"Hi, I'm Edwin. Today, I'll explain seafloor spreading rates.\" "
        "Click to go to the animation.")

    # 2 -- animation clip
    video_slide(prs, os.path.join(DEL, "video", "Spreading_Rates_Animation_Clip.mp4"),
                os.path.join(DEL, "video", "clip_poster.png"), clip["total"],
                "Auto-plays (%.1f s, silent). Voice-over lines and timings: see Narration_and_Timing_Guide.md. "
                "Ends on the paper-strip model - CUT to your on-camera demonstration here." % clip["total"])

    # 3 -- key concepts recap
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string("071A33")
    M.add_shape(slide.shapes, scene["slides"][0]["shapes"][0])  # navy background
    M.add_shape(slide.shapes, text("Heading: Summary", "Summary", 60, 60, 1000, 80, 40, bold=True, align="l"))
    ap = os.path.join(DEL, "assets_png"); os.makedirs(ap, exist_ok=True)
    sp = os.path.join(DEL, "slides_png")
    imgs = [
        crop(os.path.join(sp, "slide2_final_state.png"), (290, 93, 1770, 1080), os.path.join(ap, "concept_seafloor_spreading.png"), (1200, 800)),
        crop(os.path.join(sp, "slide3_final_state.png"), (240, 40, 1680, 1000), os.path.join(ap, "concept_half_vs_full_rate.png"), (1200, 800)),
        crop(os.path.join(sp, "slide4_magnetic_stripes_state.png"), (380, 190, 1540, 963), os.path.join(ap, "concept_magnetic_stripes.png"), (1200, 800)),
    ]
    captions = ["(a) Seafloor spreading", "(b) Half vs full rate", "(c) Magnetic stripes"]
    items = []
    for i, (cap, img) in enumerate(zip(captions, imgs)):
        x, y, w = 60 + i * 610, 190, 580
        g = slide.shapes.add_group_shape()
        pic = g.shapes.add_picture(img, M.E(x), M.E(y), M.E(w), M.E(w * 2 / 3))
        pic.name = "Figure " + cap
        M.add_shape(g.shapes, rect("Figure border", x, y, w, w * 2 / 3,
                                   ln={"color": "3A5575", "w": 2, "a": 1, "dash": None}))
        M.add_shape(g.shapes, text("Caption", cap, x, y + w * 2 / 3 + 14, w, 48, 22, color="E6EDF4", align="l"))
        g.name = "Figure " + cap
        items.append((g.shape_id, fade_in(0.2 + 0.4 * i, 0.5)))
    g = slide.shapes.add_group_shape()
    M.add_shape(g.shapes, text("Relation", "Half-spreading rate = distance from ridge ÷ age", 60, 760, 1800, 80, 30, bold=True))
    M.add_shape(g.shapes, text("Citation", "(Fowler, 2005; Vine and Matthews, 1963)", 60, 850, 1800, 44, 18, color="C9D6E3"))
    g.name = "Key relation"
    items.append((g.shape_id, fade_in(1.6, 0.5)))
    set_transition(slide, fade=True)
    put_timing(slide, M.Timing().build(items))
    slide.notes_slide.notes_text_frame.text = (
        "Recap after your demonstration (speak, don't read): seafloor spreading creates new crust at the ridge; "
        "half-rate is one side relative to the ridge, full-rate is plate separation; "
        "mirror-image magnetic stripes plus their ages give the rate (distance divided by age). Figures fade in automatically.")

    # 4 -- references end card
    video_slide(prs, os.path.join(DEL, "video", "Spreading_Rates_References_EndCard.mp4"),
                os.path.join(DEL, "slides_png", "slide5_references_end_card.png"), scene["endcard"]["adv"],
                "Auto-plays the references end card (Harvard, Cite Them Right). Hold on the last frame.")

    out = os.path.join(DEL, "Spreading_Rates_Presentation.pptx")
    prs.save(out)
    print("saved", out)


def M_solid(c, a=1.0):
    return {"type": "solid", "color": c, "a": a}


if __name__ == "__main__":
    main()
