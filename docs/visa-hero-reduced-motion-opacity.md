# Visa hero subtitle: inline opacity defeated reduced-motion override

## What was wrong
Same CSS bug class as the earlier inline-style vs media-query fix: the visa
page hero subtitle had `style="...opacity:.6..."` inline while the
`@media (prefers-reduced-motion: reduce)` block sets
`.visa-fade { opacity: 1 }` without `!important`. A class rule can never
beat an inline style, so:

- Reduced-motion users saw the subtitle permanently stuck at 60% opacity
  while every other hero element showed at full opacity (the `.visa-card`
  rule in the same media block already uses `opacity: 1 !important` for
  exactly this reason).
- Normal users had a broken fade-in start state: `.visa-fade` is supposed
  to start at `opacity: 0`, but the inline `.6` overrode it during the
  0.32s animation delay, so the subtitle flashed at 60% before animating
  .6 -> 1 instead of fading in from 0.

## Fix
Removed the inline `opacity:.6` from the subtitle in
`templates/packages/visa.html`. The `visaHeroFade` animation ends at
opacity 1 with `fill-mode: forwards`, so `.6` was never a real steady
state for anyone — removing it restores the intended 0 -> 1 fade and lets
the reduced-motion rule apply cleanly.

## How it was found
Scripted sweep of every template: collected elements carrying both a class
and an inline style, and cross-checked each inline property against @media
rules in main.css and the page's own style block that target one of the
element's classes without `!important`. This was the only live instance.
