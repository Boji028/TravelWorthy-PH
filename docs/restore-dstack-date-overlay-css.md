# Date input overlay showing double boxes site-wide (dstack/doverlay CSS accidentally deleted)

## What was wrong
Every date field using the `.dstack`/`.doverlay`/`.dstack-input` pattern —
the visa assistance modal, the package inquiry modal (mobile and desktop),
Plan My Trip, and the admin inquiries date filter — was rendering as two
stacked boxes: the styled "Select date" placeholder, with the real,
unstyled native `<input type="date">` visible directly underneath it
showing its own "mm/dd/yyyy" placeholder and calendar icon.

Traced through git history: commit `e7393b6` ("fix: make date input fully
invisible, let a plain div render the visible box", July 20) added the
`.dstack` CSS to `main.css` that makes this pattern work — the real input
is made fully invisible (`opacity: 0`, absolutely positioned) so it only
captures the tap, while the sibling `.doverlay` div renders the actual
visible box. About 4 hours later the same day, commit `311dcd3` ("fix:
tighten nav padding on mobile...") — an unrelated nav-bar spacing change —
deleted that entire CSS block as a side effect, apparently from pasting in
a full `main.css` replacement based on a slightly older local copy. The
HTML markup and `initDateDisplay()` JS (which only syncs the overlay's
text, not its positioning) were untouched and kept referencing classes
that no longer had any CSS behind them, so every affected date field has
shown the broken double-box appearance since July 20 — about 10 days,
unnoticed because nothing in the test suite renders or visually checks
CSS.

## Fix
Restored the `.dstack` / `.dstack-input` / `.doverlay` / `.doverlay.has-value`
block to `static/css/main.css`, byte-for-byte identical to what commit
`e7393b6` originally added, in the same location (between the native
date/time font-reset rule and the custom-dropdown section).

## Why the fix is correct
Diffed the restored block against `git show e7393b6:static/css/main.css`
and confirmed it's identical. This is a pure CSS restoration — no HTML or
JS changed, since those were never actually broken; they just had no CSS
to pair with. Full test suite (565 passed, 2 pre-existing/unrelated
failures) re-run after the change to confirm nothing else regressed,
though this particular bug wouldn't have been caught by the backend test
suite either way since it's a visual/CSS-only issue.