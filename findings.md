# Findings — Revivr / THE CONTRAST

## The site we are replacing

revivr.com.au is a stock WordPress fitness theme with the demo content still in it:

- Lorem ipsum in nearly every body slot, including all three pricing cards.
- Fabricated stats: "20M+ Working Hours", "100+ Completed Projects", "100K+ Happy Customers".
- Four stock trainer headshots, one of them (Amy Walker) duplicated.
- One testimonial, attributed to the same name as a trainer, with lorem ipsum as the quote.
- The blog is the untouched WordPress "Hello world!" post from 18 November 2025.
- The services section sells "Tons of Equipment" and "Modern Equipment", which is gym-theme
  boilerplate and has nothing to do with a wellness camp.

Everything real on the page fits in about six lines: the About paragraph, the sauna and yoga
one-liners, three camp locations, three prices, four partners, and the contact block. Those
are the only things carried across. Everything else in the redesign is written fresh.

## Real assets kept verbatim

- About paragraph ("The Revivr Club Wellness Camp & Day Experience takes you on a powerful
  journey…") — the only well-written copy on the site.
- "Ideal for loosening up muscles" (sauna), "Great for mind and body wellbeing" (yoga).
- Tagline "Recover – Rest – Revitalise".
- Locations: Sunshine Coast, Brisbane, Gold Coast. Address 13 Fairfax Street, Sippy Downs QLD 4556.
- Prices: $99/wk Essential Coaching Package, $75/session Coaching Session, $99/mo PT Business Coaching.
- Partners: Fitness Cartel, Recovery Room Australia, Med Infusions, One Block Back.
- Contact: 0431525118, info@revivr.com.au. Hours 07:00-22:00, seven days.

## Engine lesson: the underwater teleport

**Symptom.** Clip 2 was prompted to plunge through the surface of the dark pre-dawn lagoon.
Its junction against clip 1 scored SSIM 0.9541 (a clean pass) and its last frame chained
happily into clips 3 and 4. The film was still broken: at frame ~3 of 5 seconds it hard-cut
from the cold black lagoon into a bright turquoise tropical reef with fish, coral and midday
sun, and clips 3-5 faithfully continued that wrong world.

**Why the gate missed it.** The junction gate only compares the *ends* of adjacent clips.
A teleport that happens in the middle of a clip is invisible to it. The internal-cut scanner
is what caught it (worst consecutive SSIM 0.268, flagged `INTERNAL-CUT?`), and it was right
on all three flagged clips while the junction gate reported PASS on all three.

**Rule.** `INTERNAL-CUT?` outranks a junction PASS. Never approve a chain on junction scores
alone; look at a filmstrip of any clip the internal scan flags:

```bash
ffmpeg -i clipN.mp4 -vf "select='not(mod(n\,15))',scale=320:-2,tile=5x1" -frames:v 1 strip.jpg
```

**Cause.** "Underwater" is a strong prior. Given the word with no constraint, the model
reaches for stock tropical reef footage regardless of what the seed frame shows.

**Fix.** Name the negatives explicitly and repeat the continuity instruction. The working
prompt shape is: *continue the exact same shot, identical grade, one single unbroken take,
no cut, no scene change, same location* followed by *absolutely no coral reef, no fish, no
sand, no seabed, no turquoise water, no sunlight, no daylight*. Positive description of the
wanted world ("near-black cold blue water, almost zero visibility, only churning bubbles")
does the rest of the work.

**Escalation if prompts alone fail.** Use the `inject` hook in `storyboard.json` to
nano-banana-edit the previous clip's last frame into the world you want, and seed from the
edited frame. Costs ~4 credits versus ~22 for a wasted clip.

## Billing, measured

Balance delta on this account, `bytedance/v1-pro-image-to-video`, `--generate-audio` off:

| Item | Credits |
|---|---|
| nano-banana keyframe (16:9 PNG) | ~8 |
| 5s clip @ 480p | ~22 |

$5 = 1000 credits. A full 5-clip draft chain plus keyframe is ~118 credits (~$0.59), which
makes 480p iteration effectively free against this budget and leaves the whole envelope for
the 1080p master.
