"""Recording-guide videos: 3-2-1 countdown + animation + the line to say (Chinese, top) + English subtitle."""
import os
import subprocess

import scene4

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deliverables", "recording_guide")
os.makedirs(OUT, exist_ok=True)
LEAD = 3.0


def at(x):
    cs = int(round(x * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Now,WenQuanYi Zen Hei,58,&H0000E1FF,&H00FFFFFF,&H00000000,&HB4000000,1,0,0,0,100,100,0,0,3,14,0,8,120,120,90,1
Style: Next,WenQuanYi Zen Hei,46,&H00B0B0B0,&H00FFFFFF,&H00000000,&HB4000000,0,0,0,0,100,100,0,0,3,12,0,8,120,120,90,1
Style: Sub,Inter,40,&H00FFFFFF,&H00FFFFFF,&H64000000,&H96000000,0,0,0,0,100,100,0,0,1,1.2,2.5,2,140,140,42,1
Style: Count,Inter,260,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Hint,WenQuanYi Zen Hei,40,&H00B0B0B0,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,2,0,0,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def guide(name, video, lines, length):
    ev = [f"Dialogue: 0,{at(i)},{at(i + 1)},Count,,0,0,0,,{c}" for i, c in enumerate("321")]
    ev.append(f"Dialogue: 0,{at(0)},{at(LEAD)},Hint,,0,0,0,,先开始录音，看着倒数；动画出现、黄字亮起时开口")
    for a, b, zh, en in lines:
        ev.append(f"Dialogue: 0,{at(LEAD + max(0, a - 0.8))},{at(LEAD + a)},Next,,0,0,0,,下一句：{zh}")
        ev.append(f"Dialogue: 0,{at(LEAD + a)},{at(LEAD + b)},Now,,0,0,0,,{zh}")
        ev.append(f"Dialogue: 0,{at(LEAD + a)},{at(LEAD + b)},Sub,,0,0,0,,{en}")
    ass = os.path.join(OUT, name + ".ass")
    open(ass, "w").write(HDR + "\n".join(ev) + "\n")
    beeps = "+".join(f"between(t,{i},{i}+0.12)" for i in range(3))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", str(LEAD), "-i", "color=c=0x0A0F1A:s=1920x1080:r=30",
                    "-i", video, "-f", "lavfi", "-t", str(LEAD + length), "-i", "sine=f=880:r=48000",
                    "-filter_complex", f"[0:v][1:v]concat=n=2:v=1:a=0,ass={ass}[v];[2:a]volume='if({beeps},0.4,0)':eval=frame[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "22", "-preset", "fast", "-c:a", "aac", "-shortest",
                    os.path.join(OUT, name + ".mp4")], check=True)
    print("wrote", name)


if __name__ == "__main__":
    V = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "deliverables", "video")
    guide("录音引导_开头", os.path.join(V, "v8_intro.mp4"), scene4.INTRO_LINES, scene4.INTRO_LEN)
    guide("录音引导_结尾", os.path.join(V, "v8_closing.mp4"), scene4.CLOSING_LINES, scene4.CLOSING_LEN)
