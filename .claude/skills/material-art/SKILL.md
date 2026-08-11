---
name: material-art
description: Generate a Materials-screen icon image for a Beyond the Veil crafting material in the project's established flat-SVG art style. Use when the user asks for artwork/an image/an icon for a specific material (alchemy reagent or forge material). Do not use to invent art for a material the user hasn't named or asked for in that turn.
---

# Material art

Beyond the Veil has no image-generation API configured, so material art is
hand-illustrated as flat, low-detail SVG, the same way bestiary art is (see
`.claude/skills/bestiary-art/`). This skill is the style guide and output
contract that keeps every material's icon visually consistent with every
other's, and with the bestiary's art family.

## Before drawing

Only generate art for a material the user has explicitly named or asked for
in that turn (see the repo's `CLAUDE.md` "Content additions require
explicit permission" rule — this applies to art the same as any other
content). Never invent a new material to illustrate.

## Output contract

- Format: inline SVG, no external references, no raster.
- `viewBox="0 0 512 512"`, `width="512" height="512"`.
- Square canvas, subject roughly centered, some breathing room at the
  edges (don't bleed the main subject off-canvas — background elements
  like grass/flowers may crop at the edges, the subject itself shouldn't).
- Save to `frontend/public/materials/<slug>.svg`, where `<slug>` is the
  material's existing `slug` field exactly as returned by the materials API
  (same value `slugify()` produces in `backend/scripts/seed_dev_data.py` —
  don't hand-type a different one).
- Do **not** draw a border/frame into the artwork itself. The app applies a
  uniform black border and fixed square size in CSS (`.material-icon` in
  `frontend/src/styles/index.css`) so every material's icon matches
  regardless of its content — baking a border into the SVG would double up
  or conflict with that.
- No embedded text, watermark, or signature.

## Style guide

Flat, simple, geometric — built from basic shapes (ellipses, circles,
polygons, rounded rects) rather than intricate paths. Low detail is
correct, not a shortcut: 2-tone shading per material (a base color plus one
darker "shading" patch) is enough. Outline major shapes with
`stroke="#3a352f" stroke-width="4"` or `5` for definition (background
scenery stays unstroked) — the same outline weight/color as the bestiary,
so all game art reads as one consistent world.

Reference palette (reuse these hex values so every piece shares one
palette; extend only when a shape genuinely needs a color none of these
cover):

| Role | Hex |
|---|---|
| Sky gradient top | `#eef2df` |
| Sky gradient bottom | `#dce6c8` |
| Meadow ground | `#93a06e` |
| Ground shadow | `#7c8a5a` |
| Grass tuft | `#7c8f61` / `#4f6b47` |
| Dark accent (outlines, stems, shading) | `#3a352f` / `#2b2823` |

Pick a plant/material-specific base + shading color that fits the subject's
theme (e.g. leaf greens for a leafy plant, petal whites/creams for a
flower) — extend the palette per-subject the same way the bestiary does for
non-beast creatures, keeping only the outline weight/color and the
sky/ground family consistent.

## Scene

Default backdrop is a **meadow**, not the bestiary's forest — open grassy
ground, wildflowers and tall grass tufts instead of pine trees, so a
Materials-screen icon reads as its own distinct setting while still sharing
the same sky-gradient palette as the bestiary for family resemblance. Keep
the background simple (a sky/backdrop fill, a ground fill, a few grass/
flower shapes); the material itself should read as the clear subject.

## After drawing

Per the repo's `CLAUDE.md` verification rule, this is a browser-visible
change: launch the app (see the `run` skill), open the Materials page in
Chromium with a hero that owns the material, confirm the new icon renders
correctly inside the square bordered frame next to its row, screenshot it,
and show the screenshot to the user.
