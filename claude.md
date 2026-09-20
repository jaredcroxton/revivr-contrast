# Revivr — THE CONTRAST (project constitution)

Scroll-film redesign of the revivr.com.au home page. Built with the Fable 5
`scroll-film-studio` skill, Lane B (real generated footage, KIE Seedance chain).

## North star

One unbroken camera push: a still pre-dawn Sunshine Coast lagoon, down through the
cold plunge, and out into sauna heat. Cold blue to gold. The film *is* the therapy,
so the page teaches the protocol before a word of copy is read.

## Data schema

`pipeline/storyboard.json`

```json
{
  "concept": "string",
  "keyframe": "string  // nano-banana prompt for the opening still, 16:9",
  "clips": [
    { "id": "clipN", "chapter": "string", "prompt": "string",
      "inject": { "model": "google/nano-banana-edit", "edit_prompt": "string", "ref": "path?" } }
  ]
}
```

Chain contract (unchanged from the skill): every clip after the first seeds from the
**ffmpeg-extracted literal last frame** of the previous clip, uploaded to KIE and passed
as `image_url`. `inject` optionally replaces that seed with an edited version of it when
the world needs to be forced.

Runtime payload consumed by `index.html`:

```
frames/f_0001.jpg … f_NNNN.jpg   // 1280px wide, q:v 4, every 2nd master frame
FRAME_COUNT                       // constant in index.html, must equal the file count
--seam                            // CSS var, sampled bottom-strip hex of the final frame
```

## Architectural invariants

1. One continuous forward camera push. No reversals, no cuts, no dissolves over seams.
2. Junction SSIM is measured, never eyeballed. >= 0.88 pass. A side-by-side decides ties.
3. Internal-cut scan runs on every clip. A mid-clip teleport is a fail even when the
   junction passes, because the junction only sees the ends.
4. Frames are drawn to a canvas via `createImageBitmap` sliding window. Never
   `<video currentTime>`, never raw `drawImage(HTMLImageElement)` in the scrub loop.
5. Single monolithic `index.html`. No componentisation, no build step.
6. Real Revivr contact details only. Nothing invented that a customer could act on.
7. `--generate-audio` is never enabled. Audio triples the bill for a muted page.

## Brand

| Token | Hex | Use |
|---|---|---|
| abyss | `#04090F` | film background, footer |
| ink | `#0A131C` | the cold content section |
| ice | `#8FCFE3` | cold accent, gauge, links on dark |
| ember | `#C2551A` | warm accent on ivory |
| gold | `#E3A544` | warm accent on ink |
| ivory | `#F6F1E8` | content background |
| char | `#14120E` | body text on ivory |

Type: **Fraunces** (display, variable SOFT axis, cold sections sit at SOFT 0 and warm
sections at SOFT 40-50) with **Schibsted Grotesk** (UI and body).

Logo: a ring with a solid right half. Cold outline, hot fill, one mark.

## Maintenance log

- **Re-run the film:** `KIE_RES=1080p python3 pipeline/kie.py chain` (clips already on
  disk are skipped, so delete the ones you want regenerated first).
- **Re-assemble:** `pipeline/assemble.sh assets/clips-1080p frames clip1 clip2 clip3 clip4 clip5`,
  then set `FRAME_COUNT` in `index.html` to the printed count and `--seam` to the printed hex.
- **Verify:** `node pipeline/verify.js` for beat screenshots and the jank test.
- **Key rotation:** `KIE_API_KEY` is read from the environment, falling back to `.env`.
  Nothing is baked into the repo.
- **Serve:** copy to `/tmp` and serve from there. macOS TCC blocks preview servers from
  reading the Desktop.
