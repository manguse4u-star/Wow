# Spreading Rates (GEOL0012 video blog)

Edwin Wang, student number 25092450

## Files
| File | What it is |
|---|---|
| `Spreading_Rates_Presentation.pptx` | **The deck to record from** (4 slides, see below) |
| `video/Spreading_Rates_Animation_with_References.mp4` | Closing animation with the references card (17.8 s, 1080p30, silent). Also embedded as slide 4 |
| `Narration_and_Timing_Guide.md` | Recording plan, what to say, and voice-over cues |
| `References.md` | Harvard reference list, where each source is cited, and image sources |
| `assets_png/` | Figures used on the slides, including the simulated magnetic anomaly profile (PNG + SVG) |
| `Spreading_Rates_Animated.pptx`, `Spreading_Rates_PPT_25sec.mp4` | Earlier full version. Every diagram is an editable PowerPoint shape with native animation. Kept as a source/backup |

## Deck layout
1. **Introduction:** title, name, student number.
2. **What is a spreading rate?** Diagram plus short definitions of half- and full-spreading rate.
3. **Measuring it from magnetic stripes:** simulated anomaly profile with a caption and the typical range of rates.
4. **Closing animation and references:** plays automatically. Put this slide after your on-camera demonstration.

Slides 1–3 build with short fades and advance on click. The video on slide 4 starts by itself.

## Notes
- **PowerPoint check:** the deck has not been played in Microsoft PowerPoint, because the build environment has none. Press F5 once to confirm that slide 4's video plays.
- **Images:** all images are own work, either schematic diagrams or a simulation. Swap in real figures if you prefer, and add their sources to the reference list.
- **On-screen text vs the brief:** the coursework brief discourages explanatory sentences on screen. Slides 2–3 include short captions because you asked for them. Remove them if your marker is strict about this.

## Rebuild after edits
```bash
cd build
python3 scene.py && python3 make_pptx.py
node render.js ../deliverables          # stills, references card, closing animation, 25 s version
python3 make_figures.py && node svg2png.js ../deliverables/assets_png/simulated_magnetic_anomaly_profile.svg ../deliverables/assets_png/simulated_magnetic_anomaly_profile.png 2
python3 make_presentation.py
```
