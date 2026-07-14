# Visa assistant form: showed success when server-side validation rejected the inquiry

## What was wrong
The visa page's assistant modal posts to bookings.plan_my_trip via fetch
and treated the response as success with `r.ok || r.redirected`. But
plan_my_trip re-renders the form with HTTP 200 when InquiryForm
validation fails, so `r.ok` was true even when no inquiry was created.

The modal's own pre-checks only cover empty fields and date order -
InquiryForm additionally enforces email format, 2-100 character names,
and FullNameValidator. Any of those failing server-side (e.g. a typo'd
email) showed the user "Your request has been sent!" while nothing was
saved and no email or notification went out.

## Fix
In templates/packages/visa.html, success is now detected by
`r.redirected` alone - plan_my_trip always redirects to the tracking
page on success and never redirects on failure. A 200 without a
redirect now shows a "double-check your details" message instead of
either a false success or the generic network-error text.

## How it was found
Deploy-readiness read-through of the inquiry submission paths: compared
what plan_my_trip returns on each branch (redirect on success, 200
re-render on validation failure) against how each AJAX caller
interprets the response.
