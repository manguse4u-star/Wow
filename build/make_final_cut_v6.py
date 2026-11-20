"""Final cut v6 (documentary template).

intro animation (rendered, scene2) + narration taken from the PPT screen recording
-> on-camera demo with leader-line annotations -> closing animation + references with BGM.
Usage: make_final_cut_v6.py PPT_REC DEMO INTRO_MP4 CLOSING_MP4 BGM_WAV OUT
"""
import json
import math
import os
import subprocess
import sys

PPT, DEMO, INTRO, CLOSING, BGM, OUT = sys.argv[1:7]
HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(HERE, "..", "deliverables", "subtitles")

PPT_KEEP = [(0.90, 12.95), (13.75, 16.40), (16.95, 20.50), (20.90, 23.20)]
DEMO_KEEP = [(1.00, 2.25), (2.70, 10.80), (11.20, 13.35), (14.55, 16.70), (18.30, 22.45),
             (23.15, 24.85), (25.30, 28.65), (29.00, 33.40)]
XF = 0.3


def dur(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).decode())


def remap(t, keep):
    acc = 0.0
    for a, b in keep:
        if t < a:
            return acc
        if t <= b:
            return acc + (t - a)
        acc += b - a
    return acc


def length(keep):
    return sum(b - a for a, b in keep)


P, D, C = length(PPT_KEEP), length(DEMO_KEEP), dur(CLOSING)
OFF_DEMO, OFF_CLOSE = P - XF, P + D - 2 * XF

# ------------------------------------------------------------------ ASS
ppt_cues = [(2.00, 5.05, "Hi, I'm Edwin, student number 25092450."),
            (5.30, 6.90, "Today I'll talk about seafloor spreading rates."),
            (8.40, 12.95, "The seafloor spreading rate usually means how fast the plates on either side of a mid-ocean ridge move apart."),
            (13.85, 16.40, "It can be split into the half-spreading rate and the full-spreading rate."),
            (17.05, 20.50, "With symmetric spreading, the full rate is exactly twice the half rate."),
            (21.85, 22.95, "So how do we measure it?")]
demo_cues = [(1.2, 2.5, "This is the mid-ocean ridge."),
             (2.8, 4.9, "The two paper strips are the seafloor on either side of it."),
             (5.1, 8.1, "When I pull the strips outward, new paper comes out from here,"),
             (8.3, 10.9, "just like new oceanic crust forming at the ridge."),
             (11.3, 16.7, "As the rock cools, it records the direction of Earth's magnetic field at that time."),
             (18.35, 22.5, "The magnetic patterns on the two strips are perfectly symmetric."),
             (23.25, 28.7, "Now suppose this stripe is 100 km from the ridge and 5 million years old."),
             (29.05, 31.8, "Then the half-spreading rate is 100 km ÷ 5 million years,"),
             (31.9, 33.4, "which is 2 cm per year.")]


def at(x):
    cs = int(round(x * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


ev = []
for a, b, s in ppt_cues:
    ev.append((remap(a, PPT_KEEP), remap(b, PPT_KEEP), "Sub", "", s))
for a, b, s in demo_cues:
    ev.append((OFF_DEMO + remap(a, DEMO_KEEP), OFF_DEMO + remap(b, DEMO_KEEP), "Sub", "", s))

SC, OX = 1080 / 1280, (1920 - 720 * 1080 / 1280) / 2
fx = lambda x: OX + SC * x
fy = lambda y: SC * y
demo_t = lambda t: OFF_DEMO + remap(t, DEMO_KEEP)


def bar(x0, y0, x1, y1, w=3):
    L = math.hypot(x1 - x0, y1 - y0); px, py = -(y1 - y0) / L * w / 2, (x1 - x0) / L * w / 2
    return "m %d %d l %d %d %d %d %d %d" % (x0 + px, y0 + py, x1 + px, y1 + py, x1 - px, y1 - py, x0 - px, y0 - py)


def circle(r):
    k = 0.5523 * r
    return (f"m 0 {-r} b {k:.0f} {-r} {r} {-k:.0f} {r} 0 b {r} {k:.0f} {k:.0f} {r} 0 {r} "
            f"b {-k:.0f} {r} {-r} {k:.0f} {-r} 0 b {-r} {-k:.0f} {-k:.0f} {-r} 0 {-r}")


def annotate(t0, t1, term, desc, lx, ly, align, tips):
    """Term + grey descriptor; thin white leader lines ending in a dot (reference-video style)."""
    a, b = demo_t(t0), demo_t(t1)
    ev.append((a, b, "Anno", r"{\an%d\pos(%d,%d)\fad(220,220)}" % (align, lx, ly),
               term + r"\N{\fs28\b0\c&HF0E8E0&}" + desc))
    for (tx, ty), (sx, sy) in tips:
        X, Y = fx(tx), fy(ty)
        ev.append((a + 0.12, b, "Line", r"{\an7\pos(0,0)\fad(260,220)\p1}", bar(sx, sy, X, Y) + r"{\p0}"))
        ev.append((a + 0.12, b, "Line", r"{\an7\pos(%d,%d)\fad(260,220)\p1}" % (X, Y), circle(7) + r"{\p0}"))


def glow(t0, t1, x, y, r=46):
    a, b = demo_t(t0), demo_t(t1)
    pulses = "".join(r"\t(%d,%d,\alpha&HB0&)\t(%d,%d,\alpha&H50&)" % (i * 1000, i * 1000 + 500, i * 1000 + 500, i * 1000 + 1000)
                     for i in range(int(b - a) + 1))
    ev.append((a, b, "Glow", r"{\an7\pos(%d,%d)\blur14\alpha&H50&\fad(250,250)%s\p1}" % (fx(x), fy(y), pulses), circle(r) + r"{\p0}"))


annotate(2.8, 6.3, "Mid-ocean ridge", "cardboard", 560, 640, 6, [((330, 960), (570, 640))])
annotate(2.9, 5.0, "Seafloor", "paper strips", 1290, 560, 4, [((600, 860), (1280, 560))])
glow(6.6, 10.9, 372, 905)
annotate(6.6, 10.9, "New crust", "forms at the ridge", 1290, 600, 4, [((405, 885), (1280, 600))])
annotate(13.0, 16.7, "Magnetic stripes", "record the field's polarity", 1290, 470, 4, [((560, 700), (1280, 470))])
annotate(19.2, 22.45, "Mirror image", "same pattern on both sides", 590, 565, 6, [((90, 600), (600, 552)), ((120, 785), (600, 578))])
ev.append((demo_t(29.05), OFF_DEMO + D, "Eq", r"{\an8\pos(960,64)\fad(250,0)}", "100 km ÷ 5 Myr = 2 cm/yr"))

ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Inter,42,&H00FFFFFF,&H00FFFFFF,&H64000000,&H96000000,0,0,0,0,100,100,0,0,1,1.2,2.5,2,140,140,42,1
Style: Anno,Inter,38,&H00FFFFFF,&H00FFFFFF,&H30000000,&H64000000,1,0,0,0,100,100,0,0,1,1.6,3,5,0,0,0,1
Style: Line,Inter,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,0,1.5,7,0,0,0,1
Style: Glow,Inter,20,&H004AC1FF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Eq,Inter,54,&H00FFFFFF,&H00FFFFFF,&H5A1A0F0A,&H5A1A0F0A,1,0,0,0,100,100,0,0,3,16,0,8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
for a, b, st, tag, s in sorted(ev):
    ass += f"Dialogue: 0,{at(a)},{at(b)},{st},,0,0,0,,{tag}{s}\n"
ass_path = os.path.join(SUB, "final_cut_v6.ass")
open(ass_path, "w").write(ass)


def st(x):
    ms = int(round(x * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


subs = sorted(e for e in ev if e[2] == "Sub")
open(os.path.join(SUB, "final_cut_v6_EN.srt"), "w").write(
    "\n".join(f"{i+1}\n{st(a)} --> {st(b)}\n{s}\n" for i, (a, b, _, _, s) in enumerate(subs)))

# ------------------------------------------------------------------ graph
g = []


def apieces(inp, keep, label):
    cat = ""
    for i, (a, b) in enumerate(keep):
        n = b - a
        g.append(f"[{inp}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                 f"afade=t=in:st=0:d=0.02,afade=t=out:st={n - 0.02:.3f}:d=0.02[{label}a{i}]")
        cat += f"[{label}a{i}]"
    g.append(f"{cat}concat=n={len(keep)}:v=0:a=1[{label}araw]")


apieces(4, PPT_KEEP, "p")
cat = ""
for i, (a, b) in enumerate(DEMO_KEEP):
    n = b - a
    g.append(f"[1:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=30[dv{i}]")
    g.append(f"[1:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
             f"afade=t=in:st=0:d=0.02,afade=t=out:st={n - 0.02:.3f}:d=0.02[da{i}]")
    cat += f"[dv{i}][da{i}]"
g.append(f"{cat}concat=n={len(DEMO_KEEP)}:v=1:a=1[dv][daraw]")
g.append("[dv]split[d1][d2];[d2]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
         "boxblur=30:3,eq=brightness=-0.32:saturation=0.75[bg];[d1]scale=-2:1080[fg];"
         "[bg][fg]overlay=(W-w)/2:0,format=yuv420p,setsar=1,fps=30,settb=1/30[dv2]")
g.append(f"[0:v]trim=0:{P},setpts=PTS-STARTPTS,fps=30,format=yuv420p,setsar=1,settb=1/30[iv]")
g.append(f"[2:v]fps=30,format=yuv420p,setsar=1,settb=1/30[cv]")
clean = "highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000"
g.append(f"[paraw]{clean},apad=whole_dur={P}[pa]")
g.append(f"[daraw]{clean}[da]")
g.append(f"[3:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-26:TP=-6:LRA=7,aresample=48000,apad=whole_dur={C}[ca]")
g.append(f"[iv][dv2]xfade=transition=fade:duration={XF}:offset={OFF_DEMO:.3f}[x1];"
         f"[x1][cv]xfade=transition=fade:duration={XF}:offset={OFF_CLOSE:.3f},ass={ass_path}[v]")
g.append(f"[pa][da]acrossfade=d={XF}[y1];[y1][ca]acrossfade=d={XF}[a]")

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", INTRO, "-i", DEMO, "-i", CLOSING, "-i", BGM, "-i", PPT,
                "-filter_complex", ";".join(g), "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", OUT], check=True)
print(json.dumps({"intro": round(P, 2), "demo": round(D, 2), "closing": round(C, 2), "total": round(P + D + C - 2 * XF, 2)}))
