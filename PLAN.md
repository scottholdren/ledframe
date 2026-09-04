# KenLED v2 — Founding Plan

A higher-resolution successor to the glass-brick wall (`~/dev/kenled`):
**~4' × 3' framed display, hidden behind a mirror (or deep-black tinted)
glass face, that you talk to** — spontaneous animations from voice prompts,
no web interface. When the LEDs are off it reads as a mirror on the wall;
when they light, the image floats up through the glass.

v1 proved the pieces this builds on: offline-first firmware that caches
and plays a palette-indexed animation, and Claude-generated animations.
v2 changes the display physics, the authoring interface, and the delivery
path — **no internet, no GitHub; a USB cable inside the frame.**

---

## 1. Resolution & LED choice — the load-bearing decision

The panel is 122 × 91 cm (4:3). Strip pitch quantizes the options:

| Option | Grid | LEDs | Pitch | Strip | Notes |
|---|---|---|---|---|---|
| **A (recommended)** | **36 × 27** | **972** | 33.3 mm | 5 V WS2812B-ECO, 30 LED/m | Pitch matches 4'×3' almost exactly (120 × 90 cm active). 10× the v1 pixel count; single-pin drivable; cell size still chunky enough for a bold baffle grid |
| B | 48 × 36 | 1,728 | 25 mm | 60 LED/m cut to alternating pattern — awkward | Finer image, but needs parallel output, ~2× power, and generation payloads get heavy |
| C | 72 × 54 | 3,888 | 16.7 mm | 60 LED/m | True "display" territory; different project (parallel driving, big PSU, big JSON). Save for v3 |

**Why A**: 36×27 is a huge visual step (real silhouettes, readable text,
recognizable sprites) while keeping every proven v1 subsystem intact —
single data pin (972 LEDs ≈ 34 fps ceiling, fine for our 8–12 fps content),
the existing animation JSON format (972 cells × 48 frames = 47 KB, inside
the firmware's existing 64 KB cell budget), and one moderate PSU.
"ECO" variant strips are cheaper, dimmer, and lower-power — a feature here,
since the face glass eats brightness anyway and v1 already runs at 50%.

Construction: 27 rows of 36 LEDs cut from 30 LED/m strip, mounted on the
backboard at 33.3 mm row spacing, serpentine wiring, `FLIP_Y` as needed —
identical logic to v1, just denser.

## 2. Power (5 V system this time)

- Worst case 972 × 60 mA ≈ 58 A @ 5 V. Reality: brightness-capped and
  art-typical content draws a fraction. Spec a **5 V 60 A supply** (~$35,
  Mean Well-style enclosed frame PSU mounts inside the case) and keep
  FastLED's power limiter at ~20–25 A as the hard ceiling.
- **Power injection every ~2 rows** (5 V droops fast): a 5 V bus bar pair of
  14 AWG runs down both sides of the backboard, feeding rows alternately.
- S3 powers from a 5 V tap. Grounds common. One wall cord.

## 3. The optical stack (front to back)

```
[1] Face: two-way mirror  — or —  smoked/tinted glass      [DECIDE §4]
[2] Diffuser: frosted acrylic (P95) or diffuser film, 2-3 mm
[3] Baffle grid: light-blocking egg-crate, one cell per LED, ~15-20 mm deep
[4] LED strips on matte-black backboard
```

- **Baffle** is what makes it look like a designed display instead of a
  glow-blob: each pixel becomes a crisp lit square with zero bleed into its
  neighbor. At 33 mm pitch, 3D-print it as tiles (e.g. 6×6-cell modules,
  ~20 mm deep walls, black PETG — we have the printer and the SCAD chops)
  or laser-cut hobby foam board as a cheaper fallback.
- **Diffuser sits on top of the baffle**, as close to the face glass as
  possible — the gap between diffuser and face is what creates ghosting.
- **Cell depth ↔ evenness**: 15–20 mm between LED and diffuser at 33 mm
  pitch gives an evenly-lit cell (rule of thumb: depth ≥ half the pitch).

## 4. Face material **[DECIDE — build a 2-cell test rig first]**

| Face | Off appearance | On appearance | Notes |
|---|---|---|---|
| **Two-way mirror acrylic** (~$100–150 for 4'×3', "see-through mirror" ~70/30) | A real mirror | Pixels punch through surprisingly well; dimmer colors soften | The magic trick. Needs the cavity behind it dark (matte-black baffle + board do this). Acrylic over glass: half the weight, no shatter risk, $ savings — slight flex needs a flat frame |
| **Gray-smoked ("bronze"/"gray") acrylic** (~$80) | Deep black void | Highest contrast, colors punch hardest | The "turned-off OLED" look. Not a mirror — a black rectangle on the wall |
| Clear + mirror window film (~$25) | Mirror-ish | Slightly hazier | Cheapest way to prototype the mirror effect before committing |

Recommendation: **decide empirically for $40** — order a small sheet of
each (12"×12" samples exist), build a 2×2-cell test box with spare v1
pixels, and look at both in a lit room. The mirror is the showstopper
concept; the smoked black is the safer image-quality bet. Both lose
~40–60% of light — which is why ECO strips + brightness cap are fine.

## 5. Frame & structure

Shadow-box frame (wood or aluminum extrusion), ~70–90 mm deep total:
face glass → diffuser → baffle → strips on 6 mm MDF/ply backboard →
wiring channel + PSU + S3 in the bottom margin or a rear bump-out.
Face panel removable (front-load or rear-load) for service. Vent slots
top rear — 972 LEDs power-capped won't run hot, but give heat a path.

## 6. Electronics & firmware — mostly a port

- **Controller: ESP32-S3 DevKitC-1** (one on hand). v1 firmware carries
  over with the Wi-Fi poller swapped for a serial receiver (§7): same
  cache/play/modes, same JSON format, `NUM_LEDS=972`, `WS2812B/GRB` at 5 V
  (back to v1-strip color order — verify at first light), same
  level-shifter-if-needed data path. No Wi-Fi credentials in v2 firmware.
- One firmware tweak: raise `MAX_ANIM_BYTES` (PSRAM makes it free) so
  long loops at 972 cells fit; maybe chunked JSON parse if generation
  starts producing 100+ frame epics.
- The **v1 designer app** is still useful as an authoring/debug tool:
  raise `MAX_DIM` 32→40, paint at 36×27, export the JSON file, and send it
  over the cable with the bench `send.py`. Its Publish button stays wired
  to v1 only. Voice is v2's primary channel.

## 7. Voice authoring — the actual new build

**Architecture: the wall stays dumb; a hidden companion computer does the
talking, and they're joined by a USB cable.** The ESP32 does what v1
proved (receive → cache → play); only the receive side changes from
Wi-Fi poll to serial. The companion turns speech into animations:

```
mic (in frame) → wake word → STT → Claude (writes a GENERATOR PROGRAM)
   → sandboxed execution renders frames → validate
   → USB serial to the ESP32 (instant)   → spoken/earcon confirmation
   → saved to the Pi's local library
```

- **Hardware**: Raspberry Pi 5 (~$80) + USB conference mic or ReSpeaker
  array (~$20–60), hidden in the frame. A Mac plays the Pi's role during
  bench work — same code, same cable.
- **The key architectural insight from v1**: don't ask the model to emit
  972-cell frame JSON token by token (slow, expensive, error-prone at this
  resolution). Ask it to **write a small JS/Python generator program** —
  exactly what produced pong, the cube, nyan, matrix rain in v1 — and
  execute that locally to render the frames. Fast to generate (code is
  ~2 KB regardless of resolution), and it scales to any grid size. This is
  the session's own working method, automated.
- **Safety rails**: run generated code in a subprocess sandbox (no net,
  no fs, timeout); validate output with the same rules as v1's
  `validateDesign`; send only on pass. The wall's cached-animation
  fallback means a bad generation can never take it down.
- **Feedback channel**: small speaker for "okay, painting rain" / error
  earcons, plus the wall itself shows a "thinking" shimmer streamed live
  while Claude generates.
- **Refinement loop**: keep conversation state on the Pi so "slower" /
  "more blue" work — same history-chaining as the v1 ✨ Describe feature.
- **Library**: every accepted animation is saved on the Pi as JSON with
  its prompt and timestamp. That replaces the git history v1 got for free,
  and it's what makes "play the rain one from yesterday" possible by voice.

### Delivery: USB serial, Pi → ESP32 (decided 2026-09-04)

No network hop anywhere. Length-prefixed packets, two kinds:

1. **ANIM** — the same palette-indexed animation JSON the wall already
   parses, delivered whole. Firmware treats it exactly like v1 treated a
   fetched `current.json`: validate → cache to flash → play. Zero format
   change.
2. **FRAME** — one raw frame (972 bytes of palette indices, or 2,916
   bytes RGB) at up to ~30 fps. The ESP32 shows it immediately and falls
   back to the cached ANIM after a short timeout with no frames. This
   enables things a file channel never could: sound-reactive idle, the
   live "thinking" shimmer, and animations longer than the ESP32's RAM
   (the Pi holds the frames and streams).

**Offline rule, unchanged from v1**: the ESP32 always has the last ANIM
in flash and plays it whenever the serial link is quiet — Pi rebooting,
Claude down, cable unplugged, the wall keeps going.

Wire: the DevKitC-1's UART-bridge USB port (leaves native USB free for
flashing; native CDC also works). Bandwidth is a non-issue: a 972-byte
frame at 30 fps is ~30 KB/s. Firmware reads the port in `loop()`; the
v1 Wi-Fi poller is deleted (recoverable from v1's git history if a
network mode is ever wanted).

## 8. Budget sketch

| Item | ~$ |
|---|---|
| 7× 5 m WS2812B-ECO 30/m strip (972 + spares) | 60–80 |
| 5 V 60 A PSU + bus wire + injection taps | 50 |
| Two-way mirror acrylic 4'×3' (or smoked: ~80) | 100–150 |
| Frosted acrylic diffuser 4'×3' | 50–70 |
| Baffle: ~1.5 kg black PETG (printed as tiles) | 30 |
| Frame lumber/extrusion, backboard, paint, hardware | 60–80 |
| Raspberry Pi 5 + mic + speaker + SD | 110–140 |
| Samples/test-rig materials | 40 |
| **Total** | **≈ $500–650** |

(Controller, bucks, shifters, tools: on hand from v1.)

## 9. Build order — each step demos something

1. **Optical test box** (weekend, ~$40): 2×2 cells, spare v1 pixels, both
   face-material samples → settles mirror vs smoked with eyes, not specs.
   (Samples: `docs/samples.md`.)
2. **Serial receiver + bench rig** (can start today): fork the v1 wall
   sketch, replace the Wi-Fi poller with the ANIM/FRAME serial receiver,
   `NUM_LEDS=972`, `MAX_DIM` 32→40. Spare S3 on the desk, USB to the Mac.
   First target is the onboard pixel; then one 36-LED row from the reels.
   A Mac-side `send.py` that pushes a v1 animation file over the cable is
   the first demo.
3. **Voice pipeline on the Mac**, driving that bench rig over the same
   cable: mic → wake → STT → Claude-writes-generator → sandbox → validate
   → ANIM packet. Then FRAME streaming for the thinking shimmer. This
   de-risks the hard new part on real hardware with the real channel.
4. **Backboard + strips + power**: the big soldering weekend. First light
   at full 36×27, driven from the Mac over USB.
5. **Baffle print farm** (runs in parallel — ~14 tiles of 6×6 cells).
6. **Frame + optical stack assembly** → the mirror moment.
7. **Move the voice code to the Pi**, mount Pi + mic + speaker in the
   frame, plug the same cable into the S3, tune, done.

## 10. Open questions **[DECIDE]**
- Mirror vs smoked black (step 1 answers this).
- Wake word / name of the thing? (It's about to be a character.)
- Voice stack details: cloud STT (fast to build) vs local Whisper
  (no audio leaves the room) — start cloud, revisit.
- v1's wall keeps its own GitHub poller and designer app, untouched. If
  "one voice, two surfaces" is ever wanted, the Pi could push to v1 over
  Wi-Fi as an add-on — not in scope.
- Sound-reactive idle mode while nobody's talking to it? (Pi has the mic
  anyway; FFT → FRAME packets. Cheap given the serial channel.)

---

*Context note: the full v1 engineering record (gotchas, build flags,
verified subsystems) lives in `~/dev/kenled` — its `PLAN.md`,
`firmware/README.md`, and git history are the reference library. v2's
firmware starts as a fork of `firmware/kenled-wall`. Claude sessions started in this directory won't
inherit v1's project memory automatically; this file plus those references
are the bridge.*
