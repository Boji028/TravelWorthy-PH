# Colour Contrast Audit

Date: September 2026
Standard: WCAG 2.1 AA (4.5:1 for normal text, 3:1 for large text and UI)
Status: documented, not fixed. Brand colours are intentionally unchanged.

## Why this is open

Fixing these means darkening brand colours. That decision was made
against, so this file records the findings for later rather than
tracking work in progress. Nothing here is a bug; it is a known
trade-off between brand and readability.

## Palette ratios

Ratios of each text colour against the backgrounds it is used on.
Values below 4.5 fail for normal text, below 3.0 fail for everything.

| Text colour | on --white | on --sand | on --linen | on --teal |
|---|---|---|---|---|
| --ink #1e1610 | 17.14 | 15.60 | 14.27 | 2.26 |
| --bark #424142 | 9.77 | 8.89 | 8.13 | 1.29 |
| --teal #175968 | 7.57 | 6.89 | 6.30 | 1.00 |
| --amber #EF8233 | 2.55 | 2.32 | 2.12 | 2.97 |
| --amber-d #a86830 | 4.31 | 3.92 | 3.58 | 1.76 |
| --mist #8fa8a3 | 2.43 | 2.21 | 2.02 | 3.11 |
| --teal-d #3BB9B6 | 2.29 | 2.09 | 1.91 | 3.30 |
| --danger #c0392b | 5.23 | 4.76 | 4.35 | 1.45 |
| --success #27ae60 | 2.76 | 2.51 | 2.30 | 2.74 |
| --warning #e67e22 | 2.74 | 2.49 | 2.28 | 2.77 |
| --white #fdfaf6 | 1.00 | 1.10 | 1.20 | 7.57 |

White text on solid buttons:

| Button background | Ratio | Verdict |
|---|---|---|
| --amber | 2.65 | fails |
| --amber-d | 4.48 | large text only |
| --teal | 7.88 | passes |
| --danger | 5.44 | passes |
| --success | 2.87 | fails |
| --warning | 2.85 | fails |
| --info | 4.30 | large text only |

## Findings by impact

1. `--mist` as text, 336 uses. At 2.21:1 on sand this is the largest
   issue on the site. It carries secondary text: captions, subtitles,
   metadata, helper lines.
2. `--amber` as text, 82 uses. At 2.32:1 on sand it fails both the
   normal and large text thresholds.
3. White on `--amber` buttons at 2.65:1. Affects every primary CTA
   including Plan My Trip.
4. `--success` (9 uses) and `--warning` (6 uses) as text, both under
   2.8:1. Low volume but they carry status meaning.
5. `--teal-d` as text, 7 uses, 2.09:1 on sand.

## Options if this is revisited

- Increase font size where `--mist` is used. Large text only needs
  3:1, which `--mist` still misses on sand, so this helps only in
  places, not everywhere.
- Substitute `--amber-d` for `--amber` on small text. It is already
  in the palette so this is not a new colour.
- Darken the button fill only. The label is large and the fill is
  solid, so a small shift there is barely visible.
- Darken `--mist` and `--amber` globally. One change fixes every use
  at once and is the largest visual change.

## What passes today

`--ink`, `--bark`, `--teal` and `--danger` all pass comfortably on
light backgrounds, and white on `--teal` passes on dark. The main
body text of the site is readable; the problem is confined to
secondary and accent text.

## Method

Ratios computed from the sRGB relative luminance formula in WCAG 2.1
against the variables defined in `static/css/main.css`. Usage counts
from grep across `static/css/main.css` and `templates/`.
