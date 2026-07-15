# Add confirmation_email_failed to the inquiry xlsx export

## Context
Flagged as a design question by the last bug-hunt pass, not implemented
there on purpose: `confirmation_email_failed` was already surfaced on
the admin inquiries list (warning icon) and the public tracking page
(notice box), but not in the `.xlsx` export — which is the thing
someone doing a batch follow-up would actually be working from. Since
the whole point of tracking this flag is "let staff notice and follow
up," leaving it out of the export undercut that.

## Change
`routes/admin.py`, `export_inquiries()`: added a "Confirmation Email
Failed" column, positioned right after "Email" (grouping it with the
field it's about). Value is `"Yes"` for a failed send, blank
otherwise — blank rather than `"Yes"/"No"` so the column works as a
scannable exception flag (sort/filter for the rare non-blank rows)
instead of a wall of "No"s to read past, matching how "Special
Requests" and "Admin Response" already handle optional fields in this
same export.

**Inserting a column mid-row shifts every column after it** — this
export also has separate logic setting Excel-native date formatting by
column index (`(7, 8)` for Date From/To, `(15, 16)` for Created
At/Responded At) and a `widths` list keyed by column position. Both
needed updating to `(8, 9)` / `(16, 17)` and a new width entry, or the
date columns would have silently gotten the wrong formatting applied
to whatever ended up in their old slot instead.

## Test
Existing export tests use a flatten-the-whole-sheet helper
(`_xlsx_strings`) that checks values appear *somewhere* in the export —
robust to a column shift, but wouldn't have caught a wrong-column bug
specifically, since "Yes" appearing in the wrong cell still counts as
"Yes appears somewhere in the sheet." Added a dedicated test that
creates one failed-confirmation inquiry and one normal one, then reads
actual cell values by row to confirm the flag lands on the *correct*
row — looking up both "Confirmation Email Failed" and "Destination"
columns by header name rather than hardcoded index, so the test itself
doesn't share the same fragility being tested for.

Verified the test is meaningful, not just passing by coincidence:
temporarily reverted the row-value fix (hardcoded blank regardless of
the flag), confirmed the new test fails with exactly the predicted
mismatch, restored the fix, confirmed it passes again.

## Verification
Full suite: 566/566 passing (565 baseline + 1 new test). All existing
export tests pass unchanged, confirming the column insertion didn't
disturb anything already covered.
