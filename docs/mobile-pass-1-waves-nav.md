# Mobile responsiveness pass 1: hero waves + nav dropdown

**Date:** 2026-07-03

## Context

Start of the mobile responsiveness phase (next roadmap item before
deployment). Audit method: Chrome/Edge DevTools device mode at iPhone
SE width (375px), walking each page and fixing issues found. Before
starting, verified via the Network panel that all 400+ requests load
clean (only 200/304/302 statuses — the 302s being correct auth
redirects), and that Edge's "Tracking Prevention" console warnings
are browser privacy behavior on Cloudinary CDN images, not site bugs.

## What changed

### 1. Hero foam waves broken on phones — `templates/main/home.html`

The animated SVG waves used a fixed `background-size: 1200px 80px`.
On a 375px viewport each wave tile was 3x the screen width, so only
a stretched sliver of the curve was visible — read as a rendering
glitch rather than waves. Added a `@media (max-width: 640px)` block
scaling the pattern to `700px 44px` (full curve shape visible at
phone width) with the `twFlow` keyframe travel distance adjusted to
700px to keep the animation loop seamless. Desktop rule untouched.

### 2. Mobile nav dropdown unpolished — `static/css/main.css`

The hamburger-opened menu was a bare white box with centered stacked
links and CTA buttons crammed together. Restyled (inside the existing
`@media (max-width: 768px)` block, desktop nav unaffected):
- Full-width tappable rows with hairline dividers between links
- Left-aligned link text (easier scanning than centered)
- Drop shadow on the panel so it reads as a layer above the page
- CTA buttons (Plan My Trip, account button) rendered as distinct
  full-width centered buttons with spacing at the bottom of the menu

## What was verified working already at 375px (no changes needed)

Hero text scaling (clamp-based), search pill vertical stacking,
hamburger toggle behavior, header layout.

## Method note

All mobile fixes in this phase are wrapped in max-width media
queries, so desktop rendering is structurally unaffected — the
desktop browser never evaluates those rules. Verified after each
edit by checking both device mode and normal view.

## Next

Continue homepage audit below the hero (carousels, tiles, stats,
testimonials, CTA, footer), then packages list, package detail,
and remaining public pages.
