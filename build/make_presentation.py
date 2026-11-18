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
from scene import C, build, rect, text, rich, fade_in

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
        "Click to continue.")

    def plain_slide():
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        sl.background.fill.solid()
        sl.background.fill.fore_color.rgb = RGBColor.from_string("071A33")
        M.add_shape(sl.shapes, scene["slides"][0]["shapes"][0])  # navy background
        return sl

    def add(sl, d, items=None, t=None):
        sh = M.add_shape(sl.shapes, d)
        if items is not None:
            items.append((sh.shape_id, fade_in(t, 0.5)))
        return sh

    ap = os.path.join(DEL, "assets_png"); os.makedirs(ap, exist_ok=True)
    sp = os.path.join(DEL, "slides_png")

    # 2 -- definition (labels only, no sentences: brief rule 5) + photo slot
    slide = plain_slide(); items = []
    add(slide, text("Heading", "Spreading Rate", 60, 46, 1200, 80, 40, bold=True, align="l"))
    img = crop(os.path.join(sp, "slide3_final_state.png"), (240, 40, 1680, 1000),
               os.path.join(ap, "definition_half_vs_full_rate.png"), (1440, 960))
    pic = slide.shapes.add_picture(img, M.E(60), M.E(150), M.E(1110), M.E(740)); pic.name = "Diagram: half vs full rate"
    items.append((pic.shape_id, fade_in(0.2, 0.5)))
    add(slide, rect("Diagram border", 60, 150, 1110, 740, ln={"color": "3A5575", "w": 2, "a": 1, "dash": None}))
    add(slide, text("Credit: diagram", "Diagram: own work (symmetric example)", 60, 900, 1110, 36, 16, color="9FB3C8", align="l"), items, 0.2)
    photo = crop(os.path.join(sp, "slide4_magnetic_stripes_state.png"), (380, 190, 1540, 963),
                 os.path.join(ap, "photo_slot_placeholder.png"), (1200, 800))
    pic = slide.shapes.add_picture(photo, M.E(1230), M.E(150), M.E(630), M.E(420))
    pic.name = "PHOTO SLOT - right-click > Change Picture"
    items.append((pic.shape_id, fade_in(0.8, 0.5)))
    add(slide, rect("Photo border", 1230, 150, 630, 420, ln={"color": "3A5575", "w": 2, "a": 1, "dash": None}))
    add(slide, text("Credit: photo", "Image: own work", 1230, 580, 630, 36, 16, color="9FB3C8", align="l"), items, 0.8)
    add(slide, text("Label: half", "Half-spreading rate", 1230, 640, 630, 40, 24, bold=True, color=C["cyan"], align="l"), items, 1.4)
    add(slide, text("Label: half detail", "one plate, relative to the ridge", 1230, 688, 630, 34, 20, align="l"), items, 1.4)
    add(slide, text("Label: full", "Full-spreading rate", 1230, 752, 630, 40, 24, bold=True, align="l"), items, 2.2)
    add(slide, text("Label: full detail", "separation of the two plates", 1230, 800, 630, 34, 20, align="l"), items, 2.2)
    add(slide, text("Label: range", "Typical full rate: 2\u201315 cm/yr", 1230, 870, 630, 36, 22, bold=True, color="FFC15A", align="l"), items, 3.0)
    add(slide, text("Citation", "(Fowler, 2005; DeMets, Gordon and Argus, 2010)", 60, 940, 1110, 36, 16, color="C9D6E3", align="l"), items, 3.0)
    set_transition(slide, fade=True)
    put_timing(slide, M.Timing().build(items))
    slide.notes_slide.notes_text_frame.text = (
        "About 9 s. To use an online photo: right-click the picture on the right > Change Picture, "
        "then edit the 'Image: ...' credit line and add the source to the References slide. "
        "Then cut to your on-camera demonstration.")

    # 3 -- closing animation (with English subtitles), auto-advances to the references
    clipf = os.path.join(DEL, "video", "Closing_Animation_with_EN_subtitles.mp4")
    s3 = video_slide(prs, clipf, os.path.join(DEL, "video", "clip_poster.png"), clip["total"],
                     "Plays automatically (%.1f s) and moves on to the references. Voice-over cues: see the narration guide." % clip["total"])
    set_transition(s3, fade=True, adv_ms=int(clip["total"] * 1000))
    s3._element.find(M.qn("p:transition")).set("advClick", "0")

    # 4 -- references (editable; add your online photo sources here)
    slide = plain_slide(); items = []
    ec = scene["endcard"]
    for d in ec["shapes"][1:]:
        sh = M.add_shape(slide.shapes, d)
        items += [(sh.shape_id, e) for e in d["fx"]]
    set_transition(slide, fade=True)
    put_timing(slide, M.Timing().build(items))
    slide.notes_slide.notes_text_frame.text = (
        "Editable. If you add online photos on slide 2, add their references here in the same Harvard style "
        "(alphabetical), e.g. Author/Organisation (Year) Title of image [Photograph]. Available at: URL (Accessed: date).")

    out = os.path.join(DEL, "Spreading_Rates_Presentation.pptx")
    prs.save(out)
    print("saved", out)


def M_solid(c, a=1.0):
    return {"type": "solid", "color": c, "a": a}


if __name__ == "__main__":
    main()
