# Fix contact page 2-column layout breaking on mobile

## Problem
The contact page had zero responsive media queries anywhere (only
`prefers-reduced-motion`). `.contact-section` is a fixed
`grid-template-columns: 1fr 1.4fr` grid holding the contact-info list
on the left and the message form on the right, with no fallback for
narrow viewports.

Computed the actual column widths at a 375px phone: the contact-info
column came out to **110px** and the form column to **153px** - not
just cramped, genuinely unusable. Each contact-info item has a 44px
icon plus label/text; the form has full-width inputs, a textarea, and
a submit button, none of which can function in a 153px column.

## Fix
`templates/main/contact.html`, both scoped to
`@media (max-width: 768px)`:

- `.contact-section`: `grid-template-columns: 1fr 1.4fr` -> `1fr`
  (stacks info above form instead of squeezing them side by side),
  gap trimmed from `3rem` to `2rem`, outer margin/padding tightened
  (`4rem auto` / `0 2rem` -> `2.5rem auto` / `0 1rem`) to match the
  padding conventions used elsewhere this session.
- `.contact-form-wrap`: padding trimmed from `2rem` to `1.25rem` on
  phones, since the card is now full-width and doesn't need as much
  inset.

Stacked column width at 375px is now 343px (up from 110/153px split)
- comfortable for both the contact-info items and the form fields.

Tablet (769-1024px) and desktop are unchanged - the 1:1.4 grid still
has enough room there (roughly 295px/413px at iPad Air's 820px),
similar to other card layouts left alone earlier this session.

## Verification
- Computed exact column widths before and after with a small script
  rather than eyeballing it.
- Brace-balance check on the edited file: 60/60 matched.
- Full test suite: 512/512 passing (pure CSS additions, no Python or
  template logic touched).

No migration needed - stylesheet-only change within one template.
