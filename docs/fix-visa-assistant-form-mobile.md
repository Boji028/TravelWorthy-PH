# Fix visa assistant form: contact number bug and mobile layout

## Problem
The "Request a Visa Assistant" modal (opened from a country card's
inquire button) had two issues, seen at Samsung Galaxy S8+ (360px):

1. The Contact Number field's placeholder ("+63 9XX XXX XXXX") was
   visibly cut off, showing only "+63 9XX XXX".
2. The Full Name/Email row and the Travel Date From/To row stayed
   side-by-side even on a 360px screen, cramming each field into
   roughly 125px.

## Root causes
1. **Genuine bug, not a responsive issue.** The contact number
   `<input>` was hardcoded to `width:50%` while every other field in
   the same form uses `width:100%`. There's no reason for this field
   specifically to be half-width - it was cut off on desktop too,
   just less noticeably since there's more room to spare there.
2. **This entire modal had zero responsive treatment.** Every layout
   property (padding, grid columns) was inline `style="..."` with no
   `@media` query anywhere - confirmed the whole file had none before
   this fix.

## Fix
`templates/packages/visa.html`:

- Contact number input: `width:50%` -> `width:100%`.
- Moved the header, form-scroll, and footer's padding out of inline
  styles and into three new classes (`.visa-modal-header`,
  `.visa-form-scroll` gains a padding rule, `.visa-modal-footer`),
  each with a `768px` mobile override that trims side padding from
  `2rem` to `1.25rem`.
- Moved the two `display:grid;grid-template-columns:1fr 1fr` rows
  (Full Name/Email, Travel Date From/To) into a shared
  `.visa-form-row` class, with a mobile override collapsing to
  `grid-template-columns: 1fr` so both fields stack on phones instead
  of squeezing side by side.
- Desktop/tablet (>768px) render identically to before - same
  padding values, same 2-column grids, just now expressed as classes
  instead of inline styles so the mobile override has something to
  hook into.

## Verification
- Parsed the modal's HTML with Python's `html.parser` after editing
  (not just visual inspection) to confirm every tag closes correctly
  - stack empty, zero mismatches, 16 opening `<div>` matched by 16
    closing `</div>`.
- Brace-balance check on the edited file: 139/139 matched.
- Rendered `/packages/visa` through an actual Flask test client:
  200 OK, `visa-form-row` appears exactly 4 times (2 CSS rules + 2
  HTML usages as expected), Full Name / Travel Date From / Travel
  Date To labels all present, phone input confirmed at
  `width:100%`.
- Full test suite: 512/512 passing.

No migration needed - template-only change.
