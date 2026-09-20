# Task plan — Revivr / THE CONTRAST

Redesign the revivr.com.au home page as a scroll-film. Budget: $5 (1000 KIE credits).

## Concept

**THE CONTRAST.** One unbroken forward camera push. A still pre-dawn Sunshine Coast lagoon,
down through the black surface into the cold, then the water warms into steam and the camera
arrives inside a cedar sauna lit gold. Cold blue to warm gold, in one shot, with a live
temperature readout climbing from 17 degrees to 85 as you scroll.

Chapters: Surface, The Break, The Cold, The Turn, The Heat.

## Express checklist

### Phase 1: Blueprint
- [x] Concept chosen (THE CONTRAST, recommended, approved)
- [x] Branding decision (keep Revivr real: real name, phone, email, address, locations)
- [x] Memory files initialised (claude.md, task_plan.md, findings.md, progress.md)
- [x] Data schema locked in claude.md (storyboard.json + frame payload contract)
- [x] Source site audited, real copy salvaged, demo content catalogued (findings.md)

### Phase 2: Link
- [x] `KIE_API_KEY` present in the environment
- [x] Credit balance read: 9908.5 before the build
- [x] Handshake proven by the nano-banana keyframe returning a usable 16:9 still

### Phase 3: Architect
- [x] Layer 1 SOP: `architecture/scroll-film.md`
- [x] Layer 2 navigation: `pipeline/kie.py` chain order, junction gate, internal-cut scan
- [x] Layer 3 tools: `pipeline/kie.py`, `pipeline/assemble.sh`, `pipeline/verify.js`
- [x] Draft chain at 480p
- [x] Draft chain approved end to end (no internal cuts, no world drift)
- [x] Master chain at 1080p
- [x] Assemble master, extract frames, sample seam colour
- [x] `FRAME_COUNT` and `--seam` patched into index.html

### Phase 4: Stylize
- [x] Palette, type pairing and logo locked (claude.md)
- [x] Page built: film stage, gauge, beats, after-film sections, footer
- [x] Verified with screenshots at every beat and junction
- [x] Jank test passes (max rAF delta under 50ms)
- [ ] Jared approves the look

### Phase 5: Trigger
- [x] Served locally for review
- [ ] Deploy decision (local only, or Jared's Vercel)
- [ ] Maintenance log finalised in claude.md
