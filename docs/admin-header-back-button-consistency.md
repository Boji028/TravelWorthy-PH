# Admin header back button consistency fix

## What happened
Across the admin add/edit pages, the back button in `.admin-header` was
inconsistent in three different ways:
- Add Package / Edit Package had no back button at all — only a "Cancel"
  link buried near the submit button at the bottom of the form.
- Add Continent / Edit Continent / Add Country / Edit Country wrapped the
  title and back link in an extra flex div (`justify-content:space-between`),
  putting the back button top-right, same row as the title.
- Add Visa / Edit Visa / Add Blog had the title and back link as flat
  siblings inside `.admin-header` (which has no flex styling), so the back
  button rendered on its own line below the title.

## Decision
Standardized on the flat sibling pattern (back button below the title),
matching Add Visa / Edit Visa.

## Changes
- `templates/admin/add_package.html` — added back link (`admin.packages`)
  below the title block.
- `templates/admin/edit_package.html` — added back link (`admin.packages`)
  below the title block.
- `templates/admin/add_continent.html` — removed the flex wrapper div;
  back link now sits below the title/subtitle.
- `templates/admin/edit_continent.html` — removed the flex wrapper div;
  back link now sits below the title/subtitle.
- `templates/admin/add_country.html` — removed the flex wrapper div;
  back link now sits below the title/subtitle.
- `templates/admin/edit_country.html` — removed the flex wrapper div;
  back link now sits below the title/subtitle.

## Result
No backend/route changes. Pure template markup fix — no new tests needed.
