# Date inputs still oversized on iOS Safari after the earlier font-family fix

## What was wrong
13fcfe7 fixed the oversized date input by resetting font-family to the
system stack, since a decorative display font (Pogonia) was inflating
iOS Safari's segmented date control. That fix is correctly scoped and
wins the cascade, but real iOS Safari (confirmed via device screenshot,
not just Chrome's mobile emulator) still rendered the "From"/"To" date
fields in the inquire-package modal as an oversized, visually blank box.

Ruled out before landing on the real cause: color contrast (--mist is a
visible sage green, not near-white), a stray `appearance: none` (only
present on `select.form-control`, not date inputs), and box-sizing
(globally `border-box` via the `*` reset, so no content-box mismatch
between browsers). The remaining cause is a known WebKit limitation:
iOS's native date/time control has its own intrinsic shell sizing that
isn't fully controllable via font-family/padding/line-height/height
alone - Chrome doesn't have this limitation, which is why the emulator
looked fine.

## Fix
`static/css/main.css`: added an `@supports (-webkit-touch-callout: none)`
block after the existing date/time font-family reset. This selector
matches iOS Safari and iOS in-app browsers only (Chrome/Android don't
support `-webkit-touch-callout`), so it can't regress the already-correct
rendering elsewhere. Inside it, `-webkit-appearance: none` strips iOS's
native shell, and height/line-height/padding/background/border-radius
are set explicitly (44px height, matching Apple's minimum tap-target
guidance) so the box is fully author-controlled instead of OS-controlled.

## How it was found
Read through main.css's existing date-input rule and the inline
per-template override in inquire_package.html, checked CSS variable
values and specificity by hand, and confirmed against a real Safari
screenshot (not just Chrome DevTools mobile emulation) that the bug
persisted post-13fcfe7.