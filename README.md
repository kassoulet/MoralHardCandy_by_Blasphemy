# moral hard candy (Blasphemy, Summer Encounter 1999) - web port, stage 1

Original: `CANDYD.EXE` (DOS) / `CANDYW.EXE` (Windows), `CANDY.DAT`, `7KINGSI2.XM` (patched release: see `PATCH.TXT`). Canonical for the RE: the DOS build (PMODE/W, Watcom C++, MIDAS, VESA, PIT clock).

## Player
`cd web && python3 -m http.server 8000`. 4:3 (the demo's 512x256 picture letterboxed in 512x384, shown at an integer scale without resampling), play/pause (`p`/space), seek (slider, arrows, Home), fullscreen (`f`). `node tools/uitest.mjs` (headless Chrome, CDP): play/pause/seek/keyboard/JS-render smoke test.

## What is exact and what is not (honest section)
| Part | Status |
|---|---|
| `CANDY.DAT` container (`re/extract_dat.py`) | **exact**: 85 files extracted (59 PNG, 6 JPEG, 14 3DS, font) |
| Unpacking of `CANDYD.EXE` (`re/unpack_*.py`) | **exact** (the stub's own loader run under Unicorn) |
| Part table (14 parts, start positions, files per part) | **exact** positions read from the EXE; times derived from the XM; files from a static string-reference scan (`re/partmap.py`), not a draw trace |
| Pictures in `web/` (`web/assets/gold/*.webp`) | **the original's own output**: frames of the 512x256 surface rendered by the original code under emulation, every 0.2 s (1274 frames, 0-254.6 s), stored as lossy webp. Not a port. Rendered in 0.2 s steps from t=0: the demo keeps frame-to-frame state, so a continuous run differs in the intermediate states (t=70 s rendered alone differs from t=70 s reached in sequence). |
| Music | the original XM through libopenmpt (not MIDAS/BASS): same notes, not bit-exact mixing |
| Part 1 in JS (`web/part0.js` + `web/assets/part0.bin`, default for 0-26.5 s, checkbox "JS render") | **bit-exact on 132 of 133 stepped frames** (t=0,0.2..26.4) vs the original's output; the 133rd (t=16.6) has 246 bytes off by 1 (x87 extended precision vs JS doubles flipping a trunc at a boundary). Faithful port of the render at 0x28770 and the row blitters 0x82e05/0x82f07: graybg, streak columns `dst*v>>8`, logo2 with opacity through the engine's blend table, mhcbox on top; no fitted constants. Not traced: why the 1-pixel border stays black (taken from the golden frames). `node tools/part0test.mjs GOLDEN_RAW_DIR` |
| Part 2 te2rb in JS (`web/te2rb.js`, `web/te2rbfx.js`, recompiled `poly_gen.js`, `fill_gen.js`, `stretch_gen.js`; default for 26.5-56 s) | **bit-exact on 359 of 369 stepped frames** (t=26.6..55.9, both flash windows included) vs the original's output, the 10 former 1-pixel frames were cracks between dome polygons where the original keeps the previous frame's pixel (it never clears the target): exact when the previous frame is passed in (`Te2rb.render` takes the previous composited surface; verified on all 0.4 s and 0.2 s grid frames I have goldens for, 38.2 and 46.4 included; the 0.1 s-grid goldens 30.7, 42.3, 44.3, 49.8, 55.9 are not on disk and were not re-checked); after a seek the stale pixel is only approximated (one warm-up frame 0.04 s earlier). Literal: 0x36250 pass (camera, clipper, projection, depth buckets, textured polygons via the static recompile of 0x40660, flat additive fill 0x3fd50, AA wire 0x300a0/0x2ff80), background sprite, palette filter + 218x218 blit, scan bars, flash branch (0x2fdb0/0x2f8e0 recompiled), border clear. **Data taken from dumps, not derived:** camera key tangents, per-face light index and colour ramp, the two music event times (30.4 s, 35.2 s). Pure function of t except those stale pixels (state = previous frame), 9 ms/frame. `node tools/te2rbtest.mjs`, `node tools/te2rbfull.mjs T1,T2 RAWDIR` (RAWDIR from `tools/mkraw.py` on harness PNGs) |
| Other 12 parts | golden frames only. |
| Engine (vicky softrender, 3DS keyframe player, s-buffer) | **not ported** |

## Sync note
Parts are switched by **music-position events** (order<<8|row from MIDAS), within-part animation uses the PIT-derived demo time (double `[0x10c7e8]`). Seek = set the module position and demo time together.

See `re/NOTES.md` (running log), `WRITEUP-asm.md`, `WRITEUP-effects.md`.


## Stepped vs pure state
The original is deterministic but history-dependent (rotating objects accumulate float rounding, fades and the part scheduler keep state), so frame(t) is not a pure function of t. The golden frames are the original stepped from t=0 at 0.2 s; the JS parts 1 and 2 are pure functions of t (part 2 was checked on the stepped grids; the flash/halo state comes from the two event times). Seeking in the golden set is exact by construction; seeking in the JS part is pure and therefore approximate.

## Size note
`web/assets/gold/` (1274 webp, 23 MB) is the fallback for every part that is not ported. Once the JS port covers all parts it can be dropped from the commit; today only parts 1 and 2 are ported, so it stays.
