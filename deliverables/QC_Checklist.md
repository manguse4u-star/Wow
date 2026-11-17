# Final Quality Control (brief §9)

| # | Check | Result |
|---|---|---|
| 1 | Scientific labels and spelling | ✅ All on-screen strings: Spreading Rates · How Fast Is the Ocean Floor Moving? · Edwin Wang · Student Number: [PLACEHOLDER] · Mid-Ocean Ridge · Magma · New Oceanic Crust · Half-Spreading Rate · Full-Spreading Rate · 2 cm/yr · 4 cm/yr · relative to ridge · relative plate separation · 2 + 2 = 4 cm/yr · Illustrative values (symmetric spreading) · Magnetic Stripes · Normal Polarity · Reversed Polarity |
| 2 | Narration matches animations | ✅ Each line is timed to its animation (see `Narration_and_Timing_Guide.md`). The same lines are in the PPTX speaker notes |
| 3 | Animated segment ≈ 25 s | ✅ MP4: 750 frames at 30 fps = 25.000 s. PPTX: 5.0 + (0.5 + 6.5) + (0.5 + 6.5) + (0.5 + 5.5) = 25.0 s |
| 4 | No paragraph-length on-screen text | ✅ Labels only. The longest is a 5-word caption |
| 5 | Name and student-number placeholder at the start | ✅ Slide 1, by 3.2 s |
| 6 | Clear at 1080p / on a phone | ✅ Smallest label is 20 pt (40 px tall at 1080p); in-text citations are 18 pt. Labels are 24–48 pt. Light text on navy, dark pill behind labels on the mantle |
| 7 | Last slide transitions to the paper-strip demo | ✅ Ends on two black-and-white strips and a cardboard ridge, held still for the cut at 0:25 |
| 8 | No misconceptions | ✅ New crust forms only at the axis. Plates move away rigidly; no old crust rises from the mantle. Melting shown as mantle upwelling, with no piston. Half-rate is drawn relative to the ridge and full-rate as plate separation, with a "symmetric" caveat. Stripes are labelled by polarity, not rock colour or type |
| 9 | Credible references | ✅ Harvard (Cite Them Right): an end card after Part 2 (4 s clip + hidden PPTX slide 5), in-text citations on slides 2–4, and the full list in `References.md`. Online check of the links was blocked by this session's network, so please click each once and confirm the access date |
| 10 | Actual files delivered | ✅ PPTX, MP4, 4K PNGs, SVGs, storyboard, guide, references |

Technical checks: the PPTX passes OOXML schema validation. The MP4 is H.264 yuv420p and ffmpeg `blackdetect` found 0 black segments.

Still for you to do:
- Replace `[PLACEHOLDER]` with your student number.
- Check playback once in Microsoft PowerPoint (F5). This environment has no PowerPoint.
