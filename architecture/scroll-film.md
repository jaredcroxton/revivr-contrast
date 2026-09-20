# SOP — the Revivr scroll-film

Layer 1. Update this file before changing `pipeline/` or the scrub engine in `index.html`.

## Goal

Produce ~300 JPEG frames of one continuous camera push (pre-dawn lagoon → cold plunge →
steam → cedar sauna) and a page that scrubs them against scroll without jank.

## Inputs

- `pipeline/storyboard.json` — the keyframe prompt and five clip prompts.
- `KIE_API_KEY` in the environment (falls back to `.env`).

## Outputs

- `assets/clips-<res>/clipN.mp4` — the chained clips.
- `assets/master.mp4` — the concatenated film, `-fps_mode vfr`.
- `frames/f_%04d.jpg` — 1280px, `-q:v 4`, every 2nd master frame.
- A printed frame count and seam hex, both of which must be patched into `index.html`.

## Tool logic

1. `kie.py keyframe` — nano-banana, 16:9 PNG, opening still only.
2. `kie.py chain` — for each clip in order:
   - seed from the previous clip's ffmpeg-extracted **literal last frame**, uploaded to KIE
     (or from an `inject`-edited version of that frame when the world needs forcing),
   - generate, poll, download, retry up to 4 times (~15% of jobs fail server-side unbilled),
   - extract first and last frames,
   - **internal-cut scan**: SSIM across frames sampled every 12 within the clip,
   - **junction gate**: SSIM of previous last frame against this clip's first frame,
     plus a side-by-side JPEG.
3. `assemble.sh` — concat dropping duplicate junction frames, VFR encode, extract frames,
   sample the seam colour.
4. `verify.js` — puppeteer screenshots at every beat and junction, plus the jank test.

Clips already on disk are skipped, so a targeted regeneration means moving the bad clip and
everything after it out of `assets/clips-<res>/` and re-running `chain`.

## Edge cases and known failure modes

| Failure | Signal | Response |
|---|---|---|
| Mid-clip teleport to a different world | `INTERNAL-CUT?` from the internal scan, junction still PASS | Filmstrip the clip. Rewrite the prompt with explicit negatives and "one single unbroken take, no cut, no scene change". Regenerate. |
| "Underwater" resolves to stock tropical reef | Bright turquoise, fish, coral, midday sun | Name the negatives (no coral, no fish, no sand, no seabed, no turquoise, no sunlight) and describe the wanted water positively. |
| Grade or geometry drift across a seam | Junction SSIM 0.80-0.88 | Regenerate with "identical framing, identical colour grade. Do not change the colour grade." |
| Stochastic texture under-reads | Bubbles, steam, caustics score 0.60-0.75 yet look seamless | The number says where to look, the side-by-side decides. Do not regenerate on the number alone. |
| Frozen scrub zones | Playhead sticks at a junction | The master was encoded CFR. Re-encode with `-fps_mode vfr`. |
| Frame-by-frame stutter | Jank test max delta over 50ms | The scrub loop is decoding JPEGs synchronously. Confirm the `createImageBitmap` window is warm around the playhead. |

## Invariants

- Junction SSIM >= 0.88 passes. An `INTERNAL-CUT?` flag outranks a junction pass.
- No dissolves over a bad seam. The scrub lets the visitor park on it.
- `--generate-audio` stays off. The page is muted and audio triples the bill.
- Draft at 480p, master at 1080p, and only after the draft is approved end to end.
