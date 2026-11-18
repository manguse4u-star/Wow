# Spreading Rates (GEOL0012 video blog)

Edwin Wang, student number 25092450

## Files
| File | What it is |
|---|---|
| `Spreading_Rates_Presentation.pptx` | **Deck to record from.** Slide 1 intro · slide 2 definition + photo slot · slide 3 closing animation (auto-plays, English subtitles) · slide 4 references (editable) |
| `video/Demo_with_EN_subtitles.mp4` | Your on-camera demo, first 1 s of silence trimmed, English subtitles burned in (32.5 s). Not pushed to GitHub |
| `video/Closing_Animation_with_EN_subtitles.mp4` | Closing animation, 13.5 s (also embedded in slide 3); `Spreading_Rates_Closing_Animation.mp4` = no subtitles |
| `Narration_and_Timing_Guide.md` | Recording order, Chinese script + English subtitles, how to add an online photo |
| `subtitles/字幕对照_中英.pdf` / `.txt` | Readable bilingual subtitle table; `.srt`/`.ass` = files for editing software |
| `References.md` | Harvard list, where each source is cited |
| `Spreading_Rates_Animated.pptx` | Earlier fully editable native-animation version (backup) |

## Final edit order (~63 s)
PPT slide 1–2 (~13 s) → demo video (32.5 s) → PPT slide 3 animation (13.5 s) → slide 4 references (~4 s).

## Compliance notes
- On-screen text is limited to titles, short labels, image credits and citations (no explanatory sentences), except the English subtitles of your speech.
- Online photos are allowed if credited on the slide and listed in the references.
- Check the deck once in PowerPoint (F5): slide 3's video should play by itself and then move to slide 4.

## Rebuild after edits
```bash
cd build
python3 scene.py && python3 make_pptx.py
node render.js ../deliverables          # stills, references card, closing animation, 25 s version
python3 make_figures.py && node svg2png.js ../deliverables/assets_png/simulated_magnetic_anomaly_profile.svg ../deliverables/assets_png/simulated_magnetic_anomaly_profile.png 2
python3 make_presentation.py
```
