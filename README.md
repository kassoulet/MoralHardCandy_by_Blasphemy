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
| Other 13 parts | golden frames only. te2rb (part 2): probed, not ported: it is sprite layers (0x31030) plus projected wire lines, no triangle fill (see re/NOTES.md); 3DS camera/key survey and the 35*(t-start) timing are known; the engine's float32 camera, matrices, vertex transform and projection are reproduced **bit-exact** in Python (`re/te2rb_f32.py`, tested on ~2500 vertices); the whole wire-line pass (3D cull, frustum polygon clipper, screen clip, depth-bucket order, AA additive lines) is reproduced **pixel-exact** in Python on the 6 frames t=27.0..28.0 (`re/te2rb_wiretest.py`: 0 differing pixels vs the emulator's line calls); still missing: sprites/scan-bar/filter, and the key tangents still come from an engine dump; no JS yet |
| Engine (vicky softrender, 3DS keyframe player, s-buffer) | **not ported** |

## Sync note
Parts are switched by **music-position events** (order<<8|row from MIDAS), within-part animation uses the PIT-derived demo time (double `[0x10c7e8]`). Seek = set the module position and demo time together.

See `re/NOTES.md` (running log), `WRITEUP-asm.md`, `WRITEUP-effects.md`.


## Stepped vs pure state
The original is deterministic but history-dependent (rotating objects accumulate float rounding, fades and the part scheduler keep state), so frame(t) is not a pure function of t. The golden frames are the original stepped from t=0 at 0.2 s; the JS part 1 is a pure function of t. Seeking in the golden set is exact by construction; seeking in the JS part is pure and therefore approximate.

## Size note
`web/assets/gold/` (1274 webp, 23 MB) is the fallback for every part that is not ported. Once the JS port covers all parts it can be dropped from the commit; today only part 1 is ported, so it stays.
