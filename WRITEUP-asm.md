# moral hard candy - assembly notes

Everything here is from `CANDYD.EXE` (DOS build, Watcom C++ 32-bit flat, PMODE/W 1.33, MIDAS 0.6.2), disassembled from the image unpacked under Unicorn (`re/dis.sh START STOP`). Addresses are linear addresses in that image. Code is compiler output (Watcom, register calling convention) except the small hand-written blitters near 0x82e00..0x83c20.

## Getting the code out of the packer
PMODE/W is not a compressor you have to understand: the stub decompresses the program into extended memory and jumps to the Watcom entry (0x554ec). `re/unpack_pmodew.py` runs the stub's own loader in Unicorn with a tiny DOS/DPMI fake and dumps RAM when EIP reaches the entry. About a second, no packer knowledge needed. (A trap found on the way: the fake's DOS transfer buffer must not live where the program image lives, a buffer at 0x60000 silently overwrote libpng's filter code.)

## The clock: ms from a PIT counter without a 64-bit divide (0x2c230)
`ms = 1000 * tick / (1193181 / divisor)`. `tick` is incremented by the timer ISR (0x2bf00). The `*1000` is not a `imul`:
```
lea eax,[edx*4]; sub eax,edx      ; 3t
shl eax,3 ; add eax,edx           ; 25t
shl eax,3                          ; 200t ... then lea ecx,[eax*4]; add ecx,eax  -> 1000t
```
(`3*8+1=25`, `*8=200`, `*5=1000`), then two 32-bit `div`s: first the PIT frequency over the programmed divisor, then the scaled tick count over that. Two small divides, no floating point, and the result is an integer millisecond clock that the main loop multiplies by `0.001` to get the double `[0x10c7e8]` ("demo time in seconds"). Pausing is a flag that makes the loop skip that recomputation, which is also how the harness drives the demo at an arbitrary time.

## Part scheduler driven by music rows (0x1d630 / 0x1d800)
The demo does not use time to switch parts. The MIDAS position (`order<<8 | row`, from `0x2c1b0`) is polled by a callback (0x1d630) that appends `{position, ms}` to a 256-entry ring buffer (`0x10c8ac`, 8 bytes per entry, write index `0x10d0ac`, read index `0x10d0b0`, `& 0xff` wrap). The consumer (0x1d800) pops entries whose `ms` is due, compares the position with the current part's `[start, end)` and calls the part's virtual start/end functions, then forwards every event to the running part (vtable +0x1c), which is where beat-synchronous effects hook in. The 14 parts are 32-byte records in a table at `0x4000590`; fields: object, start position, end position, `started` byte, `done` byte, start time (double).

Consequence for the port: the demo is "a function of the music position" like the other DOS ports, but within a part the animation uses the PIT time, and some effects keep per-frame state (the harness shows frame(t) is deterministic but not independent of the frames drawn before it).

## Hand-written MMX blitters (0x82e40 ..)
The software renderer (Kaspar Daugaard's "vicky") draws into 32 bpp surfaces and uses MMX for the per-pixel work. The alpha blend at 0x82e7b..0x82ec5, two pixels per iteration:
```
movd mm0,[esi]      ; src pixel A          movd mm1,[edi]   ; dst A
movd mm2,[esi+4]    ; src pixel B          movd mm3,[edi+4] ; dst B
punpcklbw  x,mm5(0)                          ; bytes -> words
punpckhwd mm0,mm0 ; punpckhdq mm0,mm0        ; broadcast the alpha word (byte 3) to all 4 lanes
pmullw mm0,mm1 ; psrlw mm0,8                 ; dst * a >> 8
packuswb mm0,mm2 ; paddb mm0,[esi] ; pand mm6 ; movq [edi-8],mm0   ; + premultiplied src, mask the alpha byte
```
Alpha is broadcast with two unpacks instead of a shuffle table (MMX has no `pshufw` on a plain Pentium MMX), and the source is stored premultiplied (the `paddb` adds the source colour itself, no second multiply). The `>> 8` instead of `/ 255` is the usual cheap approximation. Since the product `dst * alpha` is what remains of the background, the alpha byte in these surfaces must be the transmittance (1 - a), i.e. the source is premultiplied and carries inverted alpha (inferred from the code, not checked against a texture). A scalar tail handles the odd pixel, `emms` at the end. The patch notes mention "non-MMX bugs": the release shipped with an MMX/non-MMX split and this is the MMX side.

## Fill and conversion helpers (0x83a80 ..)
* `0x83a80` solid fill: align the destination to 32 bytes with single dword stores, then a 32-byte unrolled loop of eight `mov [eax+n],edx`, with `cmp BYTE PTR [eax+0x20],dl` placed in the loop. That `cmp` is a read of the next cache line: a software prefetch for a CPU (Pentium, 1999) that does not allocate a line on write miss, so the line is already in the cache when the next iteration stores into it.
* `0x83ae9` 8-bit indexed to 32 bpp through a 256-entry table (`mov bl,[esi]; mov eax,[edx+ebx*4]`).
* `0x83b17` plain `rep movsd`.
* `0x83bb4` 32 bpp to **24 bpp packed** (VBE mode 0x4112 is 24 bpp). Four pixels (`ABCD`, 16 bytes) become three dwords (12 bytes) with `ror eax,16 / mov ah,bl / ror eax,16`-style rotates: no byte stores, no multiplies, 3 dword writes per 4 pixels, which matters because the destination is video memory.

## What the screen blit tells you
The scene is rendered at **512x256** (a 2:1 letterboxed picture inside 640x480), into a 32 bpp system-memory surface (`w,h,pitch,buf` at object +0,+4,+8,+0x10), and only the final per-scanline call through the converter (0x54d33, one indirect call per line) touches the LFB. In our emulation the destination object of that call is bogus (LFB+0x130, pitch 1) because the video manager is only half faked, which is why the first captures were black. The harness therefore reads the source surface directly (`re/harness.py`, `frame_png`).

## The two blend row functions (0x82e05 and 0x82f07)
Both are MMX loops, two pixels per iteration. 0x82e05 (`dst = (dst*A >> 8) + src`, alpha A broadcast from the source's top byte with punpckhwd+punpckhdq, pmullw, psrlw 8, packuswb, paddb, then pand 0x00ffffff) expects premultiplied sources with A = transmittance (255 - alpha). 0x82f07 adds an opacity: the dst weight comes from a 256x256 byte table indexed by [opacity][A] (looked up per pixel with movzx, because MMX has no gather) and the source is scaled by the opacity word (pmullw by a broadcast constant, psrlw 8). Sprites are drawn as spans of non-transparent pixels only, so fully transparent areas cost nothing.
