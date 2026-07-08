# Fix unusable mobile PDF requirements viewer on visa page

## Problem
Tapping "View Requirements" on a visa country card opens a modal with
an embedded `<iframe>` pointing directly at the PDF file. On phones
(tested at iPhone 14 Pro Max, 430px), the modal shrinks to fit the
screen, but the iframe still loads the browser's full native PDF
viewer UI (zoom controls, page navigation, search, its own toolbar) at
that same shrunken size - producing a tiny, barely-tappable toolbar
and PDF content that needs both horizontal and vertical scrolling to
read.

This isn't fixable with CSS: that toolbar is the browser's own PDF
renderer, not our markup, so we have no way to resize or restyle it.

## Fix
`templates/packages/visa.html`, `openPdfViewer()`: on phones
(`window.innerWidth <= 768`, matching the site's established phone
tier), skip the modal/iframe entirely and open the PDF directly in
its own tab (`window.open(url, '_blank')`) instead. Desktop and
tablet (>768px) are unchanged - the existing modal has enough room
there for the embedded viewer to actually work.

Confirmed `/uploads/<filename>` (`app.py`) serves files via
`send_from_directory` without `as_attachment=True`, so this opens the
PDF inline in the browser's full-page native PDF viewer rather than
forcing a download - mobile browsers handle that well on their own
(proper pinch-zoom, full width, no cramped embedded toolbar).

The call happens synchronously inside the button's `onclick` handler,
so it's a direct result of a user gesture and isn't blocked by popup
blockers.

## Verification
- Brace-balance check on the edited file: 131/131 matched.
- Full test suite: 512/512 passing (client-side JS change only, no
  Python or template rendering logic touched).
- Confirmed the uploads route serves PDFs inline, not as a forced
  download.

No migration needed - JavaScript-only change within one template.
