"""Assemble the final cut (v4) from the original recordings.

PPT screen recording -> on-camera demo -> closing animation (+ references),
with pauses trimmed, loudness matched, label overlays and English subtitles.
Paths to the user's recordings are passed on the command line.
"""
import json
import os
import subprocess
import sys

PPT, DEMO, CLOSING, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
SUB = os.path.join(HERE, "..", "deliverables", "subtitles")
TMP = os.environ.get("TMPDIR_CUT", "/tmp")

# ---- keep-ranges (original seconds) -------------------------------------
PPT_KEEP = [(0.90, 12.95), (13.75, 16.40), (16.95, 20.50), (20.90, 23.20)]
DEMO_KEEP = [(1.00, 2.25), (2.70, 10.80), (11.20, 13.35), (14.55, 16.70), (18.30, 22.45),
             (23.15, 24.85), (25.30, 28.65), (29.00, 33.40)]
CLOSING_LEN = 15.3
XF = 0.3


def remap(t, keep):
    """original time -> time in the trimmed clip (None if inside a cut)."""
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


P, D = length(PPT_KEEP), length(DEMO_KEEP)
OFF_DEMO = P - XF
OFF_CLOSE = P + D - 2 * XF
TOTAL = P + D + CLOSING_LEN - 2 * XF

# ---- subtitles + overlays (one ASS over the final timeline) -------------
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
# slide 2: short labels under the two headings, appearing when they are named
t_lab = remap(13.85, PPT_KEEP)
t_s3 = remap(20.95, PPT_KEEP)
ev.append((t_lab, t_s3, "Label", r"{\pos(1232,224)}", r"one plate,\Nrelative to the ridge"))
ev.append((t_lab + 0.8, t_s3, "Label", r"{\pos(1232,423)}", r"separation of\Nthe two plates"))
# slide 3: data credit under the simulated profile
ev.append((remap(21.4, PPT_KEEP), P, "Credit", r"{\an9\pos(1835,768)}", "Simulated profile (own work); data: Ogg (2012)"))
# demo: the key calculation as an on-screen equation
t_eq = OFF_DEMO + remap(29.05, DEMO_KEEP)
ev.append((t_eq, OFF_DEMO + D, "Eq", r"{\an8\pos(960,56)}", "100 km ÷ 5 Myr = 2 cm/yr"))

ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Liberation Sans,44,&H00FFFFFF,&H00FFFFFF,&H64000000,&H64000000,1,0,0,0,100,100,0,0,3,8,0,2,115,115,40,1
Style: Label,Liberation Sans,34,&H00F0E6DC,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: Credit,Liberation Sans,22,&H00C8B39F,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,9,0,0,0,1
Style: Eq,Liberation Sans,60,&H00FFFFFF,&H00FFFFFF,&H82000000,&H82000000,1,0,0,0,100,100,0,0,3,18,0,8,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
for a, b, st, tag, s in sorted(ev):
    fade = r"{\fad(250,0)}" if st != "Sub" else ""
    ass += f"Dialogue: 0,{at(a)},{at(b)},{st},,0,0,0,,{tag}{fade}{s}\n"
ass_path = os.path.join(SUB, "final_cut_v4.ass")
open(ass_path, "w").write(ass)

# plain readable SRT of all spoken subtitles on the final timeline
def st(x):
    ms = int(round(x * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)
subs = sorted(e for e in ev if e[2] == "Sub")
open(os.path.join(SUB, "final_cut_v4_EN.srt"), "w").write(
    "\n".join(f"{i+1}\n{st(a)} --> {st(b)}\n{s}\n" for i, (a, b, _, _, s) in enumerate(subs)))

# ---- filter graph --------------------------------------------------------
def pieces(inp, keep, vchain, label):
    parts, cat = [], ""
    for i, (a, b) in enumerate(keep):
        n = b - a
        parts.append(f"[{inp}:v]trim={a}:{b},setpts=PTS-STARTPTS{vchain}[{label}v{i}]")
        parts.append(f"[{inp}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,"
                     f"afade=t=in:st=0:d=0.02,afade=t=out:st={n - 0.02:.3f}:d=0.02[{label}a{i}]")
        cat += f"[{label}v{i}][{label}a{i}]"
    parts.append(f"{cat}concat=n={len(keep)}:v=1:a=1[{label}v][{label}a0]")
    return parts

g = []
g += pieces(0, PPT_KEEP,
            ",crop=2560:1440:0:80,scale=1920:1080:flags=lanczos,fps=30,format=yuv420p,setsar=1", "p")
g.append("[pv]delogo=x=50:y=957:w=520:h=55:enable='gte(t,%.2f)',delogo=x=1:y=994:w=358:h=76,fps=30,settb=1/30[pv2]" % remap(20.3, PPT_KEEP))
g += pieces(1, DEMO_KEEP, ",fps=30", "d")
g.append("[dv]split[d1][d2];[d2]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
         "boxblur=30:3,eq=brightness=-0.12[bg];[d1]scale=-2:1080[fg];"
         "[bg][fg]overlay=(W-w)/2:0,format=yuv420p,setsar=1,fps=30,settb=1/30[dv2]")
g.append(f"[2:v]trim=0:{CLOSING_LEN},setpts=PTS-STARTPTS,fps=30,format=yuv420p,setsar=1,settb=1/30[cv]")
# loudness: speech clean-up + EBU R128 normalisation per source
clean = "highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000"
g.append(f"[pa0]{clean}[pa]")
g.append(f"[da0]{clean}[da]")
g.append(f"[3:a]atrim=0:{CLOSING_LEN},aformat=channel_layouts=stereo[ca]")
g.append(f"[pv2][dv2]xfade=transition=fade:duration={XF}:offset={OFF_DEMO:.3f}[x1];"
         f"[x1][cv]xfade=transition=fade:duration={XF}:offset={OFF_CLOSE:.3f},ass={ass_path}[v]")
g.append(f"[pa][da]acrossfade=d={XF}[y1];[y1][ca]acrossfade=d={XF}[a]")

cmd = ["ffmpeg", "-v", "error", "-y", "-i", PPT, "-i", DEMO, "-i", CLOSING,
       "-f", "lavfi", "-t", str(CLOSING_LEN), "-i", "anullsrc=r=48000:cl=stereo",
       "-filter_complex", ";".join(g), "-map", "[v]", "-map", "[a]",
       "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", OUT]
subprocess.run(cmd, check=True)
json.dump({"ppt": P, "demo": D, "closing": CLOSING_LEN, "total": TOTAL,
           "off_demo": OFF_DEMO, "off_closing": OFF_CLOSE}, open(os.path.join(HERE, "final_cut.json"), "w"), indent=1)
print(json.dumps({"ppt": round(P, 2), "demo": round(D, 2), "total": round(TOTAL, 2)}))
