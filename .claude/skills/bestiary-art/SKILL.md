---
name: bestiary-art
description: Generate a bestiary thumbnail image for a Beyond the Veil monster in the project's established flat-SVG art style. Use when the user asks for artwork/an image/an icon for a specific monster in the bestiary. Do not use to invent art for a monster the user hasn't named or asked for in that turn.
---

# Bestiary art

Beyond the Veil has no image-generation API configured, so monster art is
hand-illustrated as flat, low-detail SVG. This skill is the style guide and
output contract that keeps every monster's art visually consistent with
every other's. `frontend/public/monsters/young-wolf.svg` is the reference
piece this guide was derived from — look at it before drawing a new one.

## Before drawing

Only generate art for a monster the user has explicitly named or asked for
in that turn (see the repo's `CLAUDE.md` "Content additions require
explicit permission" rule — this applies to art the same as any other
content). Never invent a new monster to illustrate.

## Output contract

- Format: inline SVG, no external references, no raster.
- `viewBox="0 0 512 512"`, `width="512" height="512"`.
- Square canvas, subject roughly centered, some breathing room at the
  edges (don't bleed the main subject off-canvas — background elements
  like trees may crop at the edges, the subject itself shouldn't).
- Save to `frontend/public/monsters/<slug>.svg`, where `<slug>` is the
  monster's existing `slug` field exactly as returned by the bestiary API
  (same value `slugify()` produces in `backend/scripts/seed_dev_data.py` —
  don't hand-type a different one).
- Do **not** draw a border/frame into the artwork itself. The app applies
  a uniform thick black border and fixed square size in CSS
  (`.bestiary-entry-image` in `frontend/src/styles/index.css`) so every
  monster's thumbnail matches regardless of its content — baking a border
  into the SVG would double up or conflict with that.
- No embedded text, watermark, or signature.

## Style guide

Flat, simple, geometric — built from basic shapes (ellipses, circles,
polygons, rounded rects) rather than intricate paths. Low detail is
correct, not a shortcut: 2-tone shading per creature (a base color plus one
darker "shading" patch, e.g. a saddle/back marking) is enough. Outline
major shapes with `stroke="#3a352f" stroke-width="4"` or `5` for definition
(background scenery like trees/sky stays unstroked).

Reference palette (reuse these hex values so every piece shares one
palette; extend only when a shape genuinely needs a color none of these
cover):

| Role | Hex |
|---|---|
| Sky gradient top | `#eef2df` |
| Sky gradient bottom | `#dce6c8` |
| Ground | `#93a06e` |
| Ground shadow | `#7c8a5a` |
| Distant foliage | `#7c8f61` |
| Near foliage | `#4f6b47` |
| Wood/trunk | `#5b4636` |
| Creature base fur/hide | `#9c9384` |
| Creature shading patch | `#857c6e` |
| Creature light patch (belly/muzzle) | `#eee6d5` |
| Dark accent (ears, paws, outlines, nose) | `#3a352f` / `#2b2823` |
| Eye | `#d99a3d` (amber) with `#2b2823` pupil |

A creature that isn't a beast (e.g. something undead, elemental, plant-like)
won't fit "fur/hide" tones — keep the same *structure* (base color + one
shading patch + dark accents + the same outline weight) but pick a palette
that fits its theme; keep the sky/ground/foliage colors above for any scene
with an outdoor backdrop so the setting stays consistent across the
bestiary.

## Scene

Ground the subject in a simple environment matching its flavor text/theme
(forest, cave, ruins, etc.) using flat background shapes — a sky/backdrop
fill, a ground fill, and a few simple background elements (trees, rocks) is
enough. Don't over-render the background; the creature should read as the
clear subject.

## After drawing

Per the repo's `CLAUDE.md` verification rule, this is a browser-visible
change: launch the app (see the `run` skill), open the Bestiary page in
Chromium, confirm the new thumbnail renders correctly inside the square
bordered frame next to its monster's entry, screenshot it, and show the
screenshot to the user.
