# Fix duplicate .nav-links a:hover rule overriding intended hover color

## What was wrong
`static/css/main.css` had two `.nav-links a:hover` rules. A stale one at
the top of the file (grouped with the now-unused `.btn-hero-primary`/
`.btn-hero-ghost` pre-dark-mode hero buttons) set
`color: var(--amber) !important` with a glow `box-shadow`. A second,
later rule set `background: var(--linen); color: var(--teal);` with no
`!important`. Because `!important` always wins regardless of source
order, nav links glowed amber on hover instead of the intended teal —
the later rule could never win on `color`. Same bug class as the
already-fixed `.nav-logo span` issue: a stale, forceful rule clobbering a
later, more-intended one.

## Fix
Removed the stale first rule (`static/css/main.css`, originally lines
58-61) entirely. Only the later rule remains, so nav links now hover to
`var(--linen)` background / `var(--teal)` text as intended.

## How it was found
Full-codebase audit (`docs/full-codebase-audit-2026-07-20.md`, finding F1)
— searching `main.css` for other instances of the broad-selector-with-
`!important` pattern that caused the `.nav-logo span` bug.

## Tests
None added — this is a pure visual CSS fix with no assertable behavior in
the existing Python/Jinja test suite (no rendered-CSS testing in this
project). **Manual re-check requested:** please hover over the nav links
in a browser (both desktop width and the ≤768px mobile nav) and confirm
they turn teal/linen, not amber, since this can't be verified
automatically.
