# Add site-wide dark mode with system-preference detection

## Scope
Whole site: public pages and the admin panel (they already share one
`main.css`, so no separate admin theme was needed). Toggle auto-follows
the device's `prefers-color-scheme` by default, with a manual override
that's remembered. Toggle buttons in the desktop nav and the mobile
menu, both touch-sized (38px).

## Variable architecture
Everything already flowed through six `:root` variables (`--sand`,
`--linen`, `--amber`, `--teal`, `--bark`, `--mist`, `--white`), so the
plan was to add a `[data-theme="dark"]` block that redefines them.
That ran into two dual-purpose conflicts worth documenting, since the
naive version of this change would have silently broken things:

**`--bark`** is used both as body text color (should flip light in
dark mode) and as a literal dark background for the footer, the
flash-info banner, and the file-upload button's hover state (should
stay dark regardless of theme). Flipping `--bark` globally would have
turned the footer white. Fix: added `--charcoal` as a new fixed
variable holding `--bark`'s original value, repointed the three
background usages to it, leaving `--bark` free to flip for text.

**`--white`** has the same problem in reverse: used both as the
site's card/surface background (should flip dark) and as literal text
color on colored buttons and flash messages - `.btn-nav`, `.btn-amber`,
`.flash.success`, etc. (must stay white regardless of theme, or button
text goes dark-on-amber). Fix: added `--surface`, seeded with
`--white`'s original value. Every `background: var(--white)` /
`background-color: var(--white)` site-wide got mechanically renamed to
`var(--surface)` (a Python regex pass, 96 replacements across 40
files - `color: var(--white)` was left untouched by the same pass, 16
occurrences). `--white` itself never changes value now.

**`--teal`** was *not* given a dark override, on purpose. It's used
as a background in several gradients (package detail banner, visa
page banners) paired with hardcoded complementary hex values - a
global swap would have shifted those gradients into an odd
bright-teal-to-navy blend. Deep teal (`#175968`) also has poor
contrast as *text* on a dark page. So instead of touching the
variable, every selector that uses `--teal` for text/border/icon
color (nav logo, active nav link, dropdown hover, `.btn-outline`,
`.mm-bell`, `.mm-login`, `.mm-links.mm-active`, `.mm-actions a`,
`.form-control:focus`) gets an explicit `[data-theme="dark"]`
override pointing at `--teal-d` (`#3BB9B6`, the existing bright-teal
hover variant) instead. Every background/gradient use of `--teal` is
untouched and looks identical in both themes.

`--amber` and the status colors (`--danger`/`--success`/`--warning`/
`--info`) were left unchanged in both themes - they're used as
saturated, self-contained backgrounds with their own paired text
color, and already have adequate contrast on a dark page.

## Dark palette
```
--sand:    #1a1815   (page background)
--linen:   #262219   (secondary surface / hover tint)
--bark:    #ede7dc   (body text)
--mist:    #a9bdb8   (muted text)
--surface: #242019   (card/nav/form background)
--ink:     #f0ece2   (form input text)
```
Warm charcoal rather than neutral gray or blue-black, to stay in the
same family as the brand's sand/linen palette instead of reading as a
generic dark theme bolted on.

## Other fixes made along the way
A few hardcoded hex colors would have broken under the new system
(text that would've gone invisible, or surfaces that wouldn't adapt),
found by grepping for literal hex/white/black values outside the
variable system:
- `.mm-name` and `.mm-links a` used hardcoded `#1a1a1a` / `#333` text
  color, sitting on what becomes a dark panel - switched to `var(--bark)`.
- `.nav-links a.active` and `.mm-links a.mm-active` had a hardcoded
  light-teal tint background (`#e8f3f1` / `#eaf4f2`) - added a
  `[data-theme="dark"]` override using a translucent `--teal-d` tint.
- `.file-upload-btn` used literal `white`/`var(--bark)` for its base
  and hover states - switched to `var(--surface)` / `var(--charcoal)`.
- `admin/base_admin.html`: `.admin-sidebar` and `.admin-mobile-toggle`
  used `var(--bark)`/`var(--sand)` as fixed-dark chrome (same
  dual-purpose issue as above) - repointed to `--charcoal`/`--white`.
  `.admin-main` used a hardcoded `#f7f2ec` background instead of
  `var(--sand)` - fixed. The "Admin Panel" sidebar label used
  `var(--sand)` for text, which would go dark-on-dark once `--sand`
  flips - switched to `var(--white)`.
- Eight admin/public list pages (`continents`, `countries`,
  `packages`, `users`, `visa`, `inquiries` x2, `contact_messages`,
  `my_inquiries`) had a near-identical hardcoded table-row-hover
  background (`#faf6f0` / `#fafaf8` / `#fffbf5`) - all pointed at
  `var(--linen)`.
- `admin/edit_package.html`: hardcoded `#f0ebe3` image placeholder
  background - pointed at `var(--linen)`.

**Deliberately left alone:** status badges (`.badge-pending`,
`.badge-confirmed`, etc.) and the small green/red pastel tag badges
scattered across reviews/package-detail/visa templates keep their
hardcoded light pastel backgrounds in both themes - they're
self-contained (own background + own text color, not inherited from
page theme) and this matches how the rest of the site already treats
status colors. A couple of very low-opacity accent tints (`.badge-closed`
background, notification unread row tint) got a quick dark-mode bump
since they'd have been nearly invisible on a dark page otherwise, but
weren't chased for pixel-perfect contrast beyond that.

## Toggle implementation
- Blocking inline script at the top of `<head>` in `base.html`, before
  any CSS loads: reads `localStorage.theme`, falls back to
  `matchMedia('(prefers-color-scheme: dark)')`, sets `data-theme` on
  `<html>`. Runs before first paint, so there's no flash of the wrong
  theme on load.
- `static/js/theme.js` (new): click handler shared by every toggle
  button on the page (desktop nav + mobile menu use the same
  `[data-theme-toggle]` attribute), flips `data-theme`, saves the
  choice to `localStorage`, and syncs every toggle's icon/label via
  `[data-theme-icon]` / `[data-theme-label]`. Both toggles stay in
  sync automatically since they read the same source of truth.
- Desktop: circular icon button (moon/sun) in the nav's utility area,
  next to the notification bell / user menu, 38px.
- Mobile: full-width row in the slide-down mobile menu, matching the
  existing `.mm-links` row style, with a text label ("Dark mode" /
  "Light mode") alongside the icon since there's more room there.
- Admin panel gets both automatically - `base_admin.html` extends
  `base.html` and the public nav (with the toggle) renders above the
  admin sidebar layout on every admin page.

## Verification
- Full test suite: 529/529 passing (dark mode is CSS/JS only, no
  route or model changes).
- `main.css` brace/paren balance: 162/162, 168/168.
- Flask test-client smoke check across 9 public routes plus 3 admin
  routes (logged in as an admin user): all 200, all contain the
  toggle button and the blocking theme script.

## Known follow-up items (not blocking, flagged for visibility)
- A handful of very low-opacity accent tints outside the ones listed
  above (e.g. `.badge-contacted`, `.btn-sm-edit`'s blue tint) weren't
  individually re-tuned for dark backgrounds - they still render, just
  slightly dimmer than they would with a dedicated dark value.
- The Google sign-in button on the login page intentionally keeps its
  fixed white background/black text in both themes, matching Google's
  own button styling convention.
