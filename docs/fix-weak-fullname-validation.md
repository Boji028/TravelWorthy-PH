## Fix
Added a new FullNameValidator class (same style as the existing
StrongPasswordValidator) and applied it to RegisterForm.name,
ContactForm.name, and InquiryForm.name - all three had the identical
gap. It requires at least two space-separated words, letters only
(Regexp allows accented characters, hyphens, apostrophes for names
like Dela Pena or O'Brien), each word at least 2 letters.

Deliberately does NOT require exactly 3 words (first/middle/last).
Filipino surnames are frequently two words on their own (Dela Cruz,
De Guzman, Santos Reyes) - the placeholder example "Juan Dela Cruz"
has no middle name and is already 3 tokens, so a strict 3-word rule
would reject legitimate names. Two-word minimum (first + last, however
many words the surname takes) is the safer rule.

## Files changed
- forms.py - added FullNameValidator class, applied to RegisterForm.name,
  ContactForm.name, InquiryForm.name
- tests/test_forms.py - added TestFullNameValidator (5 cases: single
  word rejected, digits rejected, short name part rejected, standard
  two-word name accepted, two-word Filipino surname accepted)
- tests/test_public_pages.py - TestContactRoute fixtures used a
  single-word name ("Juan") in the success-path tests; updated to
  "Juan Dela Cruz" so they still exercise a valid submission

## Verification
- Full suite: 490 passed, 0 failed (485 existing + 5 new).