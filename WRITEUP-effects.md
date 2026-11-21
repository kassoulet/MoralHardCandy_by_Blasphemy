# moral hard candy - the effects

Blasphemy (feat. MD[tpolm]), Summer Encounter 1999. Music: `7kingsi2.xm` (51 orders, 259.7 s). Engine: "vicky's softrender engine" by Kaspar Daugaard (software rasteriser with flat/gouraud/textured/perspective modes, s-buffer, z-buffer, 8 and 32 bpp textures, blending filters), a 3DS loader with keyframes and a material manager, libpng 1.0.2 and a JPEG decoder for the 59 PNG and 6 JPEG textures. Everything is in `CANDY.DAT` (85 files, bytes XOR 0x2a: see `re/extract_dat.py`).

## Format of the show
* It renders at **512x256** (2:1) and the DOS build centres that in a 640x480 24 bpp mode, so the intended picture has black bars. The player shows it letterboxed in 4:3.
* 14 parts, switched by **music row** (`order<<8|row`), see WRITEUP-asm.md. Each part is a C++ class with a constructor that loads its own textures and 3DS scene (so the loading screen counts parts), a start/end hook, a render(t) and an event hook for the music.
* Part table (positions from the EXE, times computed from the XM; `web/assets/parts.json`) and the DAT files each part's code names (`re/partmap.py`, `web/assets/partfiles.json`):

| # | music position | time | what you see | files it loads |
|---|---|---|---|---|
| 1 | 0x0000-0x0409 | 0-26.5 s | dark screen, three grey group logos fading in over vertical streaks | graybg, mhcbox, logo2 |
| 2 | 0x0409-0x0b00 | 26.5-56 s | orange fly-through with a thin black frame, bright light sweeps | kasser, dna, offrun, te2rb.3ds |
| 3 | 0x0b00-0x0f00 | 56-75.2 s | flying over blue glass hexagon prisms | biku2, sekskant, cirkmat, knap1-4, bikube2.3ds |
| 4 | 0x0f00-0x1202 | 75.2-92.3 s | yellow/black rings, a tunnel of arcs | y-files, ringe.3ds |
| 5 | 0x1202-0x1600 | 92.3-112.9 s | grey harbour photo with a field of blue shards, "take me away" | havn2, takeaway, boxpipe2.3ds |
| 6 | 0x1600-0x1800 | 112.9-124.1 s | orange background, a ring of glowing particles, circles | handfun2, flare1, ring23 |
| 7 | 0x1800-0x1d00 | 124.1-148.1 s | glass tube in an orange tunnel, "md - jaakko manninen" credit | bluebg, streger, stregerl, circlex, md, byter, slyde, lysobj.3ds |
| 8 | 0x1d00-0x1e00 | 148.1-154.5 s | photo of a walking child, big "walking" caption | kage.jpg, magnet, patt, manboy, walking, flares.3ds |
| 9 | 0x1e00-0x2010 | 154.5-165.7 s | spiky yellow translucent object on a dark circuit-board background | vly4, valser, spiff1.3ds, 4xbold.3ds |
| 10 | 0x2010-0x2400 | 165.7-184.9 s | white hexagonal frame with striped border, orange light rays | babs2b, sugarlov, belien, cirkel1-4, volum.3ds |
| 11 | 0x2400-0x2500 | 184.9-191.3 s | rotating gold logo mark in a dotted-ring tunnel (grey industrial photo behind) | industr1.jpg, skriver1, belien, bluedot, sortcirk, cigar.3ds, flarec |
| 12 | 0x2500-0x2910 | 191.3-212.1 s | glowing blue-white sphere with a scrolling greetings text ("we would like to say hello to ...") | inout.jpg, hulstrim, ioright, drugpush, kaspar2, glowsph.3ds |
| 13 | 0x2910-0x2c00 | 212.1-224.9 s | glowing green sphere and black spiky star sprites (the `snefnug` textures) over orange | orange, flarec, snefnug1-4 |
| 14 | 0x2c00-0x3200 | 224.9-254.7 s | orange cloth/torso with the "blasphemy - so like candy" logo, fading out over streaked checkers | scrollbg, checkers, blogo1, boxphere.3ds |

(The descriptions come from the captured frames, `web/assets/gold/`; the "files" column is a static string-reference scan of each part's own functions, not a trace of what is drawn, so a file listed may be used by the neighbouring part sharing a function.)

## Look
Two things give the demo its look. First, almost every part is a **3DS scene played with its keyframes** (camera path, object position/rotation/scale tracks) drawn translucent: glass hexagons, tubes, shards, a spiky ball. The renderer blends 32 bpp surfaces with the MMX alpha routine (WRITEUP-asm.md). Second, **photographic textures** (the 1024-ish JPEGs and the 512x256 PNGs) are used as backgrounds and as environment maps and are drawn through horizontal-line distortion and cross-fades, the "video noise" strips visible on the harbour and walking parts.

## How the port stands (what is exact, what is not)
* Golden frames: exact. `web/assets/gold/g%04d.webp` are the frames the original's own code produced under emulation (the 32 bpp surface it renders, lossy webp for size), one every 0.2 s of demo time, stepped in order from 0 with the music-row events fed as the MIDAS callback would. They are the original's output, but rendered in 0.2 s steps: the demo keeps frame-to-frame state, so a continuous 25/50 fps run draws different intermediate states (a re-render of t=70 s alone differs from the same t reached through the stepped sequence).
* Part 1 (title) in JS (`web/part0.js`): **approximate**. Black surface, `logo2.png` (300x90) at (106,83), premultiplied alpha, times a fade curve. The fade is a table fitted to the golden frames (it is a function of the demo time, near-linear with a kink at about 3 s and 18 s), not derived from the code. Mean absolute difference inside the logo box against the golden frames: 0.2 at 2 s, 0.5 at 6 s, 1.5 at 10 s, 2.2 at 14 s, 4.0 at 18 s, 5.1 at 20 s (levels 0-255; the original also draws vertical streaks that are not modelled, and after about 21 s it adds more). `node tools/part0test.mjs` prints these.
* Everything else: not ported. A bit-exact JS version means porting the whole software rasteriser and the 3DS keyframe player; the original code is available as readable disassembly (`re/dis.sh`) and the emulator gives golden output to diff against, but that is a larger job than one session.

## Part 1 (title), decoded and ported bit-exact
Layers, in order, on a 512x256 surface: graybg.png; the column streaks (each column's byte v[x] multiplies the background, `dst*v>>8`, v = clamp(255*(0.1 * sum of five sin/cos terms of x and time + (min(0.01491 t,3) - 0.3)))); the logo2 sprite faded in from 2 s (opacity min(1,(t-2)*0.03822)*0.3, applied through a 256x256 blend table); the mhcbox frame on top. The JS port (`web/part0.js`) matches 132 of 133 stepped golden frames byte for byte and the last differs by 1 in 246 bytes.

## te2rb frame anatomy (probe, not ported)
A te2rb frame is six or seven translucent sprite layers (large orange gradients scaled and moved over time), a black frame, white wire lines (the Tube03 edges projected through the animated camera) and flashing scan bars at the top and bottom. The engine never calls its triangle fill for this part, so the port is a sprite compositor plus a line drawer.
