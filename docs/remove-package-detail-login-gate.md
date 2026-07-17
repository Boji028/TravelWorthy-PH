# Remove login gate on package-detail inquiries

**Date:** 2026-07-17

## What changed

`templates/packages/detail.html` used to hide the inquiry form behind a
login wall - unauthenticated visitors saw a "Login to Inquire" button
linking to `/auth/login` instead of the actual inquiry form. This was
inconsistent with the rest of the site: the Visa page (`Inquire Now`)
and Plan My Trip both already let guests inquire with no account,
and the backend route (`routes/bookings.py::inquire_package`) never
required login either - it already accepts `user_id=None` for guest
inquiries. Package detail was the one place a guest actually got
blocked from reaching the form.

**Fix:** removed the `{% if current_user.is_authenticated %} ... {%
else %} Login to Inquire {% endif %}` conditional. The "Inquire Now"
button now always opens the inquiry modal, for guests and logged-in
users alike - matching Visa and Plan My Trip.

Left alone: the separate, unrelated login gate further down the same
page for leaving a *review* (still requires an account - reasonable,
since reviews should be tied to an identifiable user).

## Tests

Added `test_guest_sees_inquire_button_not_login_gate` in
`tests/test_packages_detail.py` - asserts an anonymous request to a
package detail page sees "Inquire Now" and never "Login to Inquire".

Full suite: 569 passed (568 previous + 1 new), 2 pre-existing warnings
unrelated to this change.
