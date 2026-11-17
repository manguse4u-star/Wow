# Spreading Rates — Part 1 animation package (GEOL0012)

| Deliverable | File |
|---|---|
| A. Editable, animated PowerPoint (16:9, 4 slides, auto-timed, 25.0 s) | `Spreading_Rates_Animated.pptx` |
| B. Animation video (1920×1080, 30 fps, 750 frames, 25.000 s, H.264, silent) | `Spreading_Rates_PPT_25sec.mp4` |
| C. Slide PNGs (3840×2160, final state of each slide) | `slides_png/` |
| C. Vector diagrams (SVG, final state of each slide, editable in Illustrator/Inkscape) | `assets_svg/` |
| C. Storyboard frames, one per second (1080p) | `storyboard/` |
| D. Narration script and exact timing | `Narration_and_Timing_Guide.md` (narration lines are also in each slide's Speaker Notes) |
| E. References (Harvard, Cite Them Right) | `References.md` |
| References end card, 4 s (place at the very end of the video, after Part 2) | `Spreading_Rates_References_EndCard.mp4` · `slides_png/slide5_references_end_card.png` · hidden slide 5 in the PPTX |
| Final QC against brief §9 | `QC_Checklist.md` |

## What is in the PPTX
- Every graphic is a native, editable PowerPoint shape: freeform cross-sections, arrows, rectangles, ovals, and text boxes (Arial). The plates are grouped ("Left plate", "Right plate"), and every shape is named in the Selection Pane.
- Real PowerPoint animations, all auto-run ("With Previous" + delay): Fade, Wipe (From Bottom/Left/Right), Split (Vertical Out), custom Motion Paths (linear, or with smooth start/end), and Fade exits.
- Slide 5 holds the References end card. It is **hidden**, so playing the deck or exporting it as video still gives exactly the 25 s Part 1. In-text citations sit on slides 2–4.
- Slide timing: slide 1 advances after 5.0 s. Slides 2–4 use a 0.5 s **Fade** transition, then advance after 6.5 s, 6.5 s and 5.5 s. Total = 25.0 s.
- **Edit view looks busier than playback.** Shapes sit at their *pre-animation* positions. On slide 4, for example, all stripe bands are stacked at the ridge because they move outward during the show. Use Slide Show or the Animation Pane to see the real result.

## How the MP4 was made, and limitations
- This environment has **no Microsoft PowerPoint**, so the MP4 was **not** exported by PowerPoint. Both files are generated from one timeline (`build/scene.py`):
  - `build/make_pptx.py` writes the shapes and native animation XML into the PPTX.
  - `build/render.js` plays the same shapes and effects frame by frame in headless Chromium and encodes them with ffmpeg.
  
  The video therefore matches the deck's choreography, but small visual details may differ from PowerPoint's own playback: wipe-edge softness, glow and soft-edge look, and font rasterisation.
- The PPTX passes OOXML schema validation and opens correctly in LibreOffice. Its animation playback has **not** been tested in Microsoft PowerPoint here.

### To re-export the video from PowerPoint yourself (optional)
1. Open `Spreading_Rates_Animated.pptx` and press F5 to check playback.
2. Go to File → Export → Create a Video → **Full HD (1080p)** → **Use Recorded Timings and Narrations**. The slide timings are already stored in the file.
3. If PowerPoint shows a slightly different total length, adjust Transitions → *After* on each slide (targets: 5.0 / 6.5 / 6.5 / 5.5 s).
4. Before exporting, replace `[PLACEHOLDER]` on slide 1 with your student number. In the MP4, the number has to be overlaid in your video editor, or the clip re-rendered (see below).

### Rebuild everything (after editing `build/scene.py`)
```bash
cd build
python3 scene.py            # writes scene.json (and checks every animation ends before its slide advances)
python3 make_pptx.py        # -> deliverables/Spreading_Rates_Animated.pptx
node render.js ../deliverables   # -> MP4, slide PNGs, SVGs, storyboard (needs playwright + ffmpeg)
```
To put your student number in, edit the `"Student Number: [PLACEHOLDER]"` string in `scene.py` and rebuild.

## Editing-suite tips
- Final order: Part 1 MP4 (0:00–0:25) → you on camera (0:25–1:00) → `Spreading_Rates_References_EndCard.mp4` (4 s). The end card is a credit-style reference frame, not narration, so it should not count as content overrun; if your marker counts every second, trim Part 2 by 2–3 s.
- Lay the voice-over on the MP4 using the timings in the guide.
- Cut to camera at exactly 0:25.00. The last 0.2 s holds still on the paper-strip model, which gives you a clean cut point.
- Fonts: Arial is used for maximum compatibility (Aptos is missing from older Office installs). To switch to Aptos, change `FONT` in `scene.py`.
