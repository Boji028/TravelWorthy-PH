# Add background image to Contact Us hero

**Date:** 2026-07-19

## Why

After removing the message form, the Contact Us page felt too plain -
just a flat teal gradient banner above the reach-us-details card.

## What changed

`templates/main/contact.html` - `.page-hero` background changed from
a flat gradient to a teal gradient layered over a photo:

```css
.page-hero {
  background: linear-gradient(135deg, rgba(59, 185, 182, .82), rgba(23, 89, 104, .88)),
    url("{{ url_for('static', filename='images/beach.jpg') }}") center / cover no-repeat;
  ...
}
```

Used `static/images/beach.jpg` - already in the repo and already the
site's own default homepage hero fallback image (see
`templates/main/home.html`), so this adds zero new dependencies or
licensing questions and stays visually consistent with the rest of
the site. The gradient overlay uses the same teal brand colors
(`--teal-d` / `--teal`) at reduced opacity so the white "Get In
Touch" heading and the decorative wave stay fully readable over the
photo.

## Tests

Ran `tests/test_public_pages.py` (16 tests, including
`TestContactPage`) - all pass, confirming the page still renders
correctly with the new background.
