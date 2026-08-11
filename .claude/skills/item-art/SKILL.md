---
name: item-art
description: Generate a Backpack-screen icon image for a Beyond the Veil equipment item or consumable, resting on a wooden table, in the project's established flat-SVG art style. Use when the user asks for artwork/an image/an icon for a specific item or consumable. Do not use to invent art for an item/consumable the user hasn't named or asked for in that turn.
---

# Item art

Beyond the Veil has no image-generation API configured, so item art is
hand-illustrated as flat, low-detail SVG, the same way bestiary and material
art are (see `.claude/skills/bestiary-art/` and `.claude/skills/material-art/`).
This skill is the style guide and output contract that keeps every item's
and consumable's icon visually consistent with every other's, and with the
rest of the game's art family.

This skill covers **both** equipment items and consumables — they share the
same wooden-table scene and style, just saved to different folders (see
below).

## Before drawing

Only generate art for an item or consumable the user has explicitly named
or asked for in that turn (see the repo's `CLAUDE.md` "Content additions
require explicit permission" rule — this applies to art the same as any
other content). Never invent a new item/consumable to illustrate.

## Output contract

- Format: inline SVG, no external references, no raster.
- `viewBox="0 0 512 512"`, `width="512" height="512"`.
- Square canvas, subject roughly centered, some breathing room at the
  edges (don't bleed the main subject off-canvas).
- Save equipment items to `frontend/public/items/<slug>.svg`; save
  consumables to `frontend/public/consumables/<slug>.svg` — `<slug>` is the
  template's existing `slug` field exactly as returned by the API (same
  value `slugify()` produces in `backend/scripts/seed_dev_data.py` — don't
  hand-type a different one). Check whether the thing you're drawing comes
  from `ITEM_TEMPLATES` or `CONSUMABLE_TEMPLATES` in that file to know which
  folder it belongs in.
- Do **not** draw a border/frame into the artwork itself. The app applies a
  uniform black border and fixed square size in CSS (`.item-icon` in
  `frontend/src/styles/index.css`) so every icon matches regardless of its
  content — baking a border into the SVG would double up or conflict with
  that.
- No embedded text, watermark, or signature.

## Style guide

Flat, simple, geometric — built from basic shapes (ellipses, circles,
polygons, rounded rects) rather than intricate paths. Low detail is
correct, not a shortcut: 2-tone shading per object (a base color plus one
darker "shading" patch, or a lighter highlight patch) is enough. Outline
major shapes with `stroke="#3a352f" stroke-width="4"` or `5` for
definition — the same outline weight/color as the bestiary and materials,
so all game art reads as one consistent world.

Reference palette (reuse these hex values so every piece shares one
palette; extend only when a shape genuinely needs a color none of these
cover):

| Role | Hex |
|---|---|
| Wood table (base) | `#b98956` |
| Wood table (plank shading) | `#a3703f` |
| Wood table (light grain streak) | `#cf9f6c` |
| Dark accent (outlines, shading) | `#3a352f` / `#2b2823` |

Pick an object-specific base + shading/highlight color that fits the
subject (wood tones for a wooden weapon, dulled metal for a ring, cloudy
glass tones for a potion, etc.) — extend the palette per-subject the same
way the other two skills do for non-default subjects, keeping only the
outline weight/color and the wood-table backdrop consistent.

## Scene

Default backdrop is a **wooden table**, not the bestiary's outdoor scene or
the materials' meadow — a warm wood-grain surface (a base fill plus a few
darker plank-line strokes/streaks for texture) filling the frame, viewed
close-up as a still life. Rest the object on top with a soft flattened
contact-shadow ellipse beneath it (same idea as the ground-shadow ellipse
used under bestiary/material subjects). No sky or wall is needed — this is
an indoor, tabletop close-up, unlike the other two skills' outdoor scenes.

## After drawing

Per the repo's `CLAUDE.md` verification rule, this is a browser-visible
change: launch the app (see the `run` skill), open the Backpack page (and,
for equipped items, the Overview page too) in Chromium with a hero that
owns the item/consumable, confirm the new icon renders correctly inside the
square bordered frame next to its row, screenshot it, and show the
screenshot to the user.
