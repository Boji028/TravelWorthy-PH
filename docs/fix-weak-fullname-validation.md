# Fix weak Full Name validation on registration

## Problem
QA testing found that the Full Name field on the Create Account page
accepted 1-3 letter junk input (e.g. "AB") with no error shown.

## Root cause
RegisterForm.name in forms.py only validated DataRequired and
Length(min=2, max=100) - any 2+ character string passed, including
single words, digits, or symbols.

## Fix
Added a new FullNameValidator class (same style as the existing
StrongPasswordValidator) and applied it to RegisterForm.name. It
requires at least two space-separated words, letters only (Regexp
allows accented characters, hyphens, apostrophes for names like
Dela Pena or O'Brien), each word at least 2 letters.

Deliberately does NOT require exactly 3 words (first/middle/last).
Filipino surnames are frequently two words on their own (Dela Cruz,
De Guzman, Santos Reyes) - the placeholder example "Juan Dela Cruz"
has no middle name and is already 3 tokens, so a strict 3-word rule
would reject legitimate names. Two-word minimum (first + last, however
many words the surname takes) is the safer rule.

## Files changed
- forms.py - added FullNameValidator class, applied to RegisterForm.name
- tests/test_forms.py - added TestFullNameValidator (5 cases: single
  word rejected, digits rejected, short name part rejected, standard
  two-word name accepted, two-word Filipino surname accepted)

## Verification
- Full suite: 490 passed, 0 failed (485 existing + 5 new).

## Follow-up (not yet applied)
ContactForm.name and InquiryForm.name have the identical weak
validation (Length only, no word-count or character check). Same fix
could be applied there if wanted.