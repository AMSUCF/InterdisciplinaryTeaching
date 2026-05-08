# Week 1 reveal.js slide deck — design

**Date:** 2026-05-08
**Course:** ENG 6813 (Interdisciplinary Teaching), Summer C 2026
**Scope:** Build a reveal.js slide deck for Week 1 from `additions/weekoneslides.txt`, host it on GitHub Pages, and arrange for it to be embedded in the Week 1 Canvas page via the existing `canvas_sync` tool. Canvas push is performed manually by the instructor after live preview, not as part of the build step itself.

## Goals

- A self-contained reveal.js deck for Week 1 that uses the course materials in `additions/weekoneslides.txt` (course overview, DH-pedagogy quotes, AI-pedagogy quotes, three images).
- Visual coherence with the course site (same fonts, color tokens, light/dark theme behavior).
- A reusable mechanism — adding `slides: <slug>` to a week's frontmatter automatically embeds the deck in that week's Canvas page when `canvas_sync push` runs.
- No code changes that impact weeks without `slides:` set.

## Non-goals

- Building decks for weeks 2–12 in this pass. Only Week 1 is scoped.
- Automated deploy/CI checks beyond what GitHub Pages already provides.
- PDF or screenshot exports of the deck.
- Vendoring reveal.js. We load it from a CDN.

## Architecture

### File layout

**New files:**
- `slides/week-01/index.html` — the reveal.js deck. Self-contained HTML page; loads reveal.js + custom theme from CDN; contains all slide `<section>` elements inline.
- `slides/week-01/images/ai-policy.png` — copy of `additions/ai-policy.png` (Mollick's syllabus AI policy).
- `slides/week-01/images/smbc-prompt.png` — copy of `additions/smbc-prompt.png` (SMBC webcomic, thematically related to Mollick prompt-quality quote).
- `slides/week-01/images/xkcd-disclaimer.png` — copy of `additions/xkcd-disclaimer.png` (xkcd webcomic, thematically related to Mollick accuracy/bias quote).
- `assets/css/reveal-theme.css` — custom theme overriding reveal.js defaults; pulls in the same Google Fonts and CSS custom properties as the site.

**Modified files:**
- `weeks/week-01.md` — gain a `slides: week-01` frontmatter field. Body content unchanged.
- `canvas_sync/models.py` — `Week` gains optional `slides` slug; gains `slides_section_html(base_url)` helper.
- `canvas_sync/parser.py` — passes `slides` value from frontmatter into `Week`.
- `canvas_sync/__main__.py` — in `_push_week`, when `week.slides` is set, splice the iframe HTML into the page body before the first `<h2>` heading.
- `canvas_sync/config.py` — `Config` gains optional `slides_base_url` (default: `https://anastasiasalter.net/InterdisciplinaryTeaching/slides/`).
- `canvas_config.example.yaml` — document the new optional `slides_base_url` field.
- `tests/` — one new unit test asserting parser reads `slides:` and that the body splicer inserts the iframe block before the first `<h2>`.

The `additions/` folder remains in the repo as the source-of-record for the slide outline; it is not deleted.

### Source-of-truth flow

```
weekoneslides.txt  →  slides/week-01/index.html  →  GitHub Pages (live URL)
                                                          ↓
                       weeks/week-01.md (slides: week-01)
                                ↓
                       canvas_sync push  →  Canvas page (iframe → live URL)
```

The Canvas page only ever holds iframe markup; slide content has one canonical copy in `slides/week-01/index.html`.

## reveal.js loading

- reveal.js CSS and JS are loaded from `cdn.jsdelivr.net` (pinned to the latest 5.x release at build time). Specific version pin is set in `index.html` and documented near the script tag.
- reveal.js's structural stylesheet (`reveal.css`) is loaded; cosmetic theme stylesheets (`white.css`, `black.css`, etc.) are *not* loaded. The custom `assets/css/reveal-theme.css` plays the role of the theme.
- Plugins: none required for the initial deck. Speaker notes are supplied via `<aside class="notes">` and use reveal.js's built-in notes support (no plugin needed for the `s`-key speaker view).

## Custom theme (`assets/css/reveal-theme.css`)

- Loaded after `reveal.css` so its rules win.
- Imports the same Google Fonts as `assets/css/style.css`: Press Start 2P, VT323, Source Serif 4, Source Sans 3.
- Borrows the site's CSS custom properties (`--bg`, `--fg`, `--accent`, `--muted`, etc.) and applies them to reveal.js targets: `.reveal`, `.reveal h1/h2/h3`, `.reveal blockquote`, `.reveal section img`, `.reveal .controls`, `.reveal .progress`, `.reveal .slide-number`.
- Light/dark variants drive off `data-theme="light"` / `data-theme="dark"` on `<html>`, the same attribute the rest of the site uses.
- Reveal-specific rule highlights:
  - `.reveal h1` — Press Start 2P, scaled down (default reveal heading sizes will overflow with this font).
  - `.reveal blockquote` — Source Serif 4 body, left-rule accent, VT323 attribution line below.
  - `.reveal section img` — `max-height: 80vh`, no border by default; webcomic slides get a 2px solid accent border via a per-section class.
  - `.reveal .controls`, `.reveal .progress` — accent color from token.
  - `.reveal .slide-number` — VT323, muted color.
- An in-deck dark-mode toggle button (top-right of viewport) flips `data-theme` on `<html>` (values: `light` / `dark`) and persists to `localStorage` under the key `theme` — the same key, attribute name, and values the site's `assets/js/theme.js` uses. Because the deck and site share an origin (`anastasiasalter.net`), they share `localStorage` and stay in sync.
- The site's `trail.js` cursor effect is **not** loaded inside the deck.

## Slide structure

Vertical (down-arrow) stacks are used for long-quote slides: a lead-in slide naming the source/topic, then a sub-slide with the quote body. Image slides and short slides do not stack.

**Part 1 — Course overview (8 horizontal positions):**

1. **Title** — "ENG 6813: Interdisciplinary Teaching" / Salter & Stanfill / Summer C 2026.
2. **Course Description** — short blurb from `index.md`.
3. **Overview** — bullet summary of the four "Over twelve weeks, students will…" goals.
4. **NEH Workshop Integration** — table of the six workshops + dates.
5. **Course Objectives** — the seven numbered objectives from `index.md`.
6. **Texts** — no required textbook; list of the four practitioner blogs (Mollick, Willison, Cohen, Underwood).
7. **Anthropic Subscription** — Claude Pro requirement; what it unlocks (Artifacts, Code Web).
8. **Grading** — the points table from `index.md`.

**Part 2 — DH Pedagogy (1 transition slide + 6 stacks):**

9. **Section header** — "DH Pedagogy" transition slide.
10. **Croxall & Jakacki** stack — lead-in: "Teaching as invisible labor" / quote body.
11. **Locke / DHQ — four pillars** stack — lead-in: four learning objectives / quote body.
12. **Locke — Information Literacy** stack — lead-in / ACRL six-frames quote.
13. **Locke — Digital Literacy** stack — lead-in / ALA-definition quote.
14. **Locke — Computational Analysis** stack — lead-in / methods-list quote.
15. **Rushkoff** stack — lead-in: "Program or Be Programmed" / quote body.

**Part 3 — AI in the classroom (3 image slides interleaved with 3 Mollick stacks):**

16. **Image** — `ai-policy.png` (Mollick's syllabus AI policy).
17. **Mollick — "Without training, everyone uses AI wrong"** stack.
18. **Image** — `smbc-prompt.png` (SMBC webcomic).
19. **Mollick — "Students understand accuracy and bias issues"** stack.
20. **Image** — `xkcd-disclaimer.png` (xkcd webcomic).
21. **Mollick — "AI is everywhere already"** stack.

**Closing:**

22. **Week 1 to-do recap** — Activity Verification due Fri May 15, Discussion (introductions) due Sun May 17, optional NEH Workshop 1 on May 13. (Not in the source outline; added as a wrap-up beat.)

**Total:** 22 horizontal positions, ~9 of which are 2-slide stacks. ~31 reveal.js sections total.

**Speaker notes:** every quote slide carries `<aside class="notes">` with the citation (Locke 2017, Croxall & Jakacki, Mollick *One Useful Thing* + URL). Webcomic slides carry attribution (SMBC / xkcd, with link) in the speaker notes plus a small visible credit line on the slide.

## Frontmatter, parser, and Canvas push integration

### Frontmatter contract

```yaml
---
week: 1
title: "Welcome and Interdisciplinary Teaching"
starts: 2026-05-11
slides: week-01          # NEW — slug pointing to slides/<slug>/
workshop: ...
assignments: ...
discussion: ...
---
```

The value is a slug (directory name under `slides/`), not a URL. The full URL is built from `slides_base_url` in `canvas_config.yaml` (defaults to `https://anastasiasalter.net/InterdisciplinaryTeaching/slides/`).

### Code changes

**`canvas_sync/models.py`:**
- `Week` gains `slides: Optional[str] = None`.
- New method `slides_section_html(base_url: str) -> Optional[str]` returning the iframe HTML wrapped in `<h2>Slides</h2>` and a 16:9 responsive `<div>` wrapper. Returns `None` when `slides` is unset.
- `body_html` is unchanged. The iframe is composed into the page body separately at push time.

**`canvas_sync/parser.py`:**
- Reads `meta.get("slides")` from frontmatter and passes it to `Week(...)`. No body manipulation; body markdown stays clean.

**`canvas_sync/config.py`:**
- `Config` gains optional `slides_base_url` attribute. Defaults to `https://anastasiasalter.net/InterdisciplinaryTeaching/slides/` when not present in YAML.

**`canvas_sync/__main__.py`:**
- In `_push_week`, when `week.slides` is set, call `week.slides_section_html(config.slides_base_url)` to get the iframe block, then splice it into `body_html`. Strategy: split on the first `<h2>` tag; insert slides HTML before it. If no `<h2>`, append to the end. The splicer is extracted as a small pure function (e.g., `_splice_slides(body_html, slides_html) -> str`) so it can be unit-tested without a Canvas connection.
- `local_fields = {"title": ..., "body": body_with_slides_html}`. Diff/update logic and approve/apply-all/quit flow are unchanged.

**`canvas_config.example.yaml`:**
- Add documented optional field `slides_base_url: https://anastasiasalter.net/InterdisciplinaryTeaching/slides/`.

### Iframe HTML template

```html
<h2>Slides</h2>
<div class="slides-embed" style="position:relative; padding-bottom:56.25%; height:0; overflow:hidden; max-width:100%;">
  <iframe
    src="https://anastasiasalter.net/InterdisciplinaryTeaching/slides/week-01/"
    style="position:absolute; top:0; left:0; width:100%; height:100%; border:0;"
    allowfullscreen
    loading="lazy"
    title="Week 1 Slides">
  </iframe>
</div>
<p><a href="https://anastasiasalter.net/InterdisciplinaryTeaching/slides/week-01/" target="_blank" rel="noopener">Open slides in a new tab</a></p>
```

Inline styles (not CSS classes) because Canvas strips/rewrites unknown CSS classes. The 16:9 `padding-bottom` keeps the iframe responsive in Canvas's variable column widths. The fallback link beneath the iframe handles cases where Canvas's iframe sandbox blocks fullscreen or third-party content for some accounts.

### Backwards compatibility

Weeks without `slides:` in frontmatter get exactly the body they get today. The change is additive only.

## Testing

One new unit test in `tests/`:
- Parses a fixture week file with `slides: week-01` in frontmatter.
- Asserts `Week.slides == "week-01"`.
- Asserts the body-splicer (`__main__._push_week` helper, extracted to a pure function for testability) inserts the iframe HTML block before the first `<h2>` in a sample body, and appends to the end when no `<h2>` is present.

No Canvas API connection in tests. No additional integration tests.

## Verification workflow

**Step 1 — Local browser preview.** Run `bundle exec jekyll serve`. Open `http://localhost:4000/InterdisciplinaryTeaching/slides/week-01/`. Walk every slide with arrow keys. Check: all 22 horizontal positions present and stacks navigable; image slides render at full height without overflow; webcomic credits visible; light/dark toggle works and persists; speaker view (`s`) shows citations on quote slides; no console errors.

**Step 2 — Local Canvas-page diff.** Run `python -m canvas_sync diff --week 1` to confirm the iframe block appears in the right position (between intro paragraph and `## Readings`) without unexpected diffs elsewhere. (No API write; this only previews.)

**Step 3 — Deploy to GitHub Pages and verify live URL.** Commit and push the changes. Wait for the GitHub Pages build to complete. Open the live URL `https://anastasiasalter.net/InterdisciplinaryTeaching/slides/week-01/` in a real browser (and an incognito window to rule out cache). Confirm relative `images/` paths resolve, CDN assets load over HTTPS without mixed-content warnings, and the deck looks right.

**Step 4 (deferred) — Canvas push.** *Not part of this build pass.* The instructor will run `python -m canvas_sync push --week 1` manually after viewing the live deck on GitHub Pages and confirming it is ready.

**Step 5 (deferred) — In-Canvas verification.** After Step 4, instructor opens the Week 1 page in Canvas, confirms the iframe loads, arrow navigation works inside the embed, fullscreen works, the fallback link works, and the embed proportions hold on small viewports.

### Rollback

If the embed is wrong but slide content is fine, removing `slides: week-01` from `weeks/week-01.md` and re-running `python -m canvas_sync push --week 1` returns the Canvas page to a slide-less state. The `slides/week-01/` directory and theme remain in the repo and viewable at the live URL.

## Out of scope

- Decks for weeks 2–12.
- A npm/Node toolchain or build step.
- Vendored reveal.js distribution files.
- PDF/screenshot export.
- A separate viewer site.
- CI checks beyond GitHub Pages' default build.
