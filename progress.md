# Progress — Revivr / THE CONTRAST

## Done

**Blueprint.** Audited revivr.com.au, catalogued the demo content, salvaged the six real
things on the page. Concept THE CONTRAST chosen and approved, real Revivr branding kept.
Palette, Fraunces + Schibsted Grotesk pairing, and the split-ring logo locked.

**Link.** `KIE_API_KEY` verified from the environment. Opening balance 9908.5 credits.
Handshake proven by the nano-banana keyframe returning a usable 16:9 dawn lagoon still.

**Architect.**

- 480p draft chain v1. Clip 1 clean. **Clip 2 teleported mid-clip into a bright tropical
  reef**, and clips 3-5 continued that wrong world. Junction gate passed all of them; the
  internal-cut scan caught it (0.268). Filmstrip confirmed a hard cut at frame 3.
- Rewrote clips 2-5 with explicit negatives and repeated continuity language. 480p draft v2
  came back correct: a real plunge, a bubble plume, no reef. Clip 4 drifted olive-green and
  clip 5 landed the sauna as a genuine morph rather than a cut.
- 1080p master chain. Same five prompts, all five clips usable first time. Clip 4 warmed to
  amber instead of the draft's green, which fixed the one weak link without a repair pass.
  Junctions read 0.63 to 0.88; every low score was bubble and steam texture under-reading,
  confirmed clean on the side-by-sides.
- Assembled: 601 frames of master at 1920x1088, extracted to 301 JPEGs at 1280px (17 MB).
  Seam colour `#D59A52`.

**Stylize.** Built the page: film stage with the ImageBitmap sliding-window scrubber, a
temperature gauge that runs 17 to 85 degrees as the film goes cold to hot, five beat
overlays, ambient cold motes over the opening, seam handoff into the manifesto, then the
protocol, a morning at camp, locations, pricing, partners and the footer.

## Errors found and fixed

| Problem | Cause | Fix |
|---|---|---|
| Clip 2 cut to a tropical reef | "Underwater" with no constraint is a strong stock prior | Explicit negatives plus "one single unbroken take, no cut, no scene change" |
| Canvas inset by 72px and 168px instead of full-bleed | The generic `section` padding rule was matching `#film` | Scoped the rule to `.after section` |
| Header unreadable over the ivory content | Adaptive luminance only samples the film canvas, which is gone past the film | Added a `.docked` state that turns the header solid ivory once film progress hits 1 |
| Finale copy lost against bright sauna wood | No scrim behind left-anchored text | Added `.fscrim`, a directional scrim driven by the finale beat's own alpha |
| Third beat unreadable over the white bubble plume | Text shadow alone cannot beat pure white | Radial scrim behind the centred beat text, plus a tighter shadow |
| Gauge flipped dark while sitting over dark water | It reused the header's top-strip luminance sample | Gave the gauge its own sample of the band it occupies, with a separate region on mobile |
| Temperature lagged the visual turn | Curve ramped heat too late | Reshaped the curve so 38 degrees lands with the amber steam |

## Tests

- Jank test, full scroll: `{"frames":1046,"avg":16.7,"p95":22.8,"max":30.6,"over50":0}` — **PASS**.
- Beat screenshots captured at every chapter, desktop 1440x900 and mobile 430x932.
- Junction side-by-sides inspected for all four seams.
- `window.__ready` fires on every capture, so no screenshot was taken of an unready page.

## Spend

| Stage | Credits | AUD |
|---|---|---|
| Keyframe + 480p draft v1 (5 clips) | 130 | $0.65 |
| 480p draft v2 (clips 2-5) | 100 | $0.50 |
| 1080p master (5 clips) | 350 | $1.75 |
| **Total** | **480** | **$2.40** |

Balance 9908.5 → 9428.5. Budget was $5, so $2.60 is unspent.

## Open

- Deploy decision. Local only for now, served at `http://localhost:5031`.
- The "A morning at camp" timings are illustrative and need Revivr to confirm the real ones.
