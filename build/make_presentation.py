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

    # 2 -- definition: half vs full spreading rate
    slide = plain_slide(); items = []
    add(slide, text("Heading", "What is a spreading rate?", 60, 46, 1200, 80, 40, bold=True, align="l"))
    img = crop(os.path.join(sp, "slide3_final_state.png"), (240, 40, 1680, 1000),
               os.path.join(ap, "definition_half_vs_full_rate.png"), (1440, 960))
    pic = slide.shapes.add_picture(img, M.E(60), M.E(150), M.E(1110), M.E(740)); pic.name = "Figure: half vs full rate"
    items.append((pic.shape_id, fade_in(0.2, 0.5)))
    add(slide, rect("Figure border", 60, 150, 1110, 740, ln={"color": "3A5575", "w": 2, "a": 1, "dash": None}))
    add(slide, rich("Figure caption", [[("Schematic ridge cross-section (own work). Example values; symmetric spreading assumed.", 0)]],
                    60, 906, 1110, 16, color="9FB3C8"), items, 0.2)
    add(slide, text("Term: half", "Half-spreading rate", 1230, 160, 630, 50, 26, bold=True, color=C["cyan"], align="l"), items, 0.8)
    add(slide, rich("Definition: half", [[("How fast one plate moves away from the ridge axis.", 0)]],
                    1230, 218, 630, 20), items, 0.8)
    add(slide, text("Term: full", "Full-spreading rate", 1230, 360, 630, 50, 26, bold=True, align="l"), items, 1.6)
    add(slide, rich("Definition: full", [[("How fast the two plates move apart. It equals 2 \u00d7 the half-rate only when spreading is symmetric.", 0)]],
                    1230, 418, 630, 20), items, 1.6)
    add(slide, rich("Note: units", [[("Both are usually given in cm per year.", 0)]], 1230, 600, 630, 18, color="9FB3C8"), items, 1.6)
    add(slide, text("Citation", "(Fowler, 2005; M\u00fcller et al., 2008)", 1230, 680, 630, 40, 16, color="C9D6E3", align="l"), items, 0.2)
    set_transition(slide, fade=True)
    put_timing(slide, M.Timing().build(items))
    slide.notes_slide.notes_text_frame.text = (
        "About 7 s. Say in your own words: the half-spreading rate is how fast one side moves away from the ridge; "
        "the full rate is how fast the two plates separate - double the half-rate if spreading is symmetric.")

    # 3 -- measuring it from magnetic stripes (simulated figure)
    slide = plain_slide(); items = []
    add(slide, text("Heading", "Measuring it from magnetic stripes", 60, 46, 1400, 80, 40, bold=True, align="l"))
    pic = slide.shapes.add_picture(os.path.join(ap, "simulated_magnetic_anomaly_profile.png"),
                                   M.E(60), M.E(140), M.E(1800), M.E(640))
    pic.name = "Figure: simulated magnetic anomaly profile"
    items.append((pic.shape_id, fade_in(0.2, 0.5)))
    add(slide, rich("Figure caption", [[(
        "Simulated magnetic anomaly profile (own work) for a ridge with a half-spreading rate of 2 cm/yr, "
        "using reversal ages from GTS2012 (Ogg, 2012). Real surveys show the same mirror-image pattern (Vine and Matthews, 1963).", 0)]],
        60, 800, 1800, 18, color="C9D6E3"), items, 0.6)
    add(slide, rich("Key point", [[(
        "Half-spreading rate = distance from the ridge \u00f7 age. Measured full rates range from about 2\u20134 cm/yr "
        "(Mid-Atlantic Ridge) to about 15 cm/yr (East Pacific Rise) (DeMets, Gordon and Argus, 2010).", 0)]],
        60, 900, 1800, 20), items, 1.4)
    set_transition(slide, fade=True)
    put_timing(slide, M.Timing().build(items))
    slide.notes_slide.notes_text_frame.text = (
        "About 7 s. Point out that the stripe pattern is the same on both sides, and that distance divided by age gives the rate. "
        "Then cut to camera for the paper-strip demonstration.")

    # 4 -- closing animation + references (played after the on-camera demo)
    clipf = os.path.join(DEL, "video", "Spreading_Rates_Animation_with_References.mp4")
    video_slide(prs, clipf, os.path.join(DEL, "video", "clip_poster.png"), clip["total"],
                "Plays automatically (%.1f s): seafloor spreading -> magnetic stripes -> paper-strip model -> references. "
                "Voice-over lines: see Narration_and_Timing_Guide.md." % clip["total"])

    out = os.path.join(DEL, "Spreading_Rates_Presentation.pptx")
    prs.save(out)
    print("saved", out)


def M_solid(c, a=1.0):
    return {"type": "solid", "color": c, "a": a}


if __name__ == "__main__":
    main()
