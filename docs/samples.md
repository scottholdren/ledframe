# Optical test rig — sample order (build step 1)

Goal: settle mirror vs smoked black with eyes, not specs. 2×2 cells at 33 mm
pitch, ~20 mm deep, black PETG baffle, spare v1 pixels at 50% brightness.
Hold each face + diffuser combo against the front in a lit room.

## Face candidates

| # | Sample | Spec | Source | ~$ |
|---|---|---|---|---|
| F1 | Two-way mirror acrylic, 12×12, 1/8" | 70% reflect / 30% transmit | SupremeTech B01G4MQ2VS (Amazon) or twowaymirrors.com 6×6 sample $9.95 | 10–15 |
| F2 | Two-way mirror acrylic, 12×12, 1/8", **40% transmit** | Brighter pixels, weaker mirror | SupremeTech B07XTRC7F1 (Amazon) | 10–15 |
| F3 | Gray smoked #2074 (dark), 1/8" × 12×12 | ~36% transmit | estreetplastics.com | 6.23 |
| F4 | Black LED Diffusion Acrylic, 12×12, 2.6 mm | Tint + diffusion in one layer, made for matrices | Adafruit #4594 | 9.95 |

Skipped: mirror window film (real two-way acrylic samples cost the same),
glass two-way mirror (70/11 — only 11% transmission, too dark for LEDs;
smart-mirror glass is the alternative but weighs 2× and costs 3×), gray #2064
(57% transmit — too light for a "black void").

## Diffuser candidates

| # | Sample | Note | Source | ~$ |
|---|---|---|---|---|
| D1 | White 2447 P95 matte, 1/8" × 12×12 | Classic sign diffuser, 45% transmit. Stacked behind F1 → ~13% total light. Likely too thick/blurry | canalplastic.com | ~6 |
| D2 | Photo diffusion gel pack, 10×12, 12 sheets mixed density | Thinnest option; test several densities in one buy. LED-matrix builders report thin film beats thick acrylic | Amazon B001NPC9SM | 10–15 |
| D3 | F4 doubles as diffuser | No separate layer needed for the smoked build | — | — |

**Total: ~$55–70.**

## What to look at

- Off: does F1/F2 read as a real mirror at room light? Does F3/F4 read as black?
- On: pixel punch at 50% brightness through each face + D1 vs D2.
- Ghosting: vary the diffuser→face gap 0 / 2 / 5 mm.
- Cell evenness: hotspot visible at 20 mm depth? (rule: depth ≥ pitch/2)
- Color: does 30% vs 40% mirror shift hue or crush dim colors?

## Decision it feeds

Full-size sheet, 48×36: two-way acrylic ~$100–150 (twowaymirrors.com max
49×97, use their calculator; T&T Plastic Land is pickup-only at this size),
smoked #2074 ~$80. Diffuser film for full size is a roll purchase if D2 wins.
