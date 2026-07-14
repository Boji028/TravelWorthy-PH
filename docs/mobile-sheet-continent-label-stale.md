# Mobile filter sheet: continent trigger label ignored the active filter

## What was wrong
In templates/packages/list.html the mobile sheet's continent dropdown
marks the correct option as selected server-side when the page loads
with ?continent_id=..., but the trigger label was hardcoded to
"All continents". Two visible effects on a filtered page load:

- The sheet showed "All continents" while a continent filter was
  actually active (the checkmark inside the open list disagreed with
  the trigger).
- The Apply handler builds its breadcrumb label from the trigger text,
  so re-applying without touching the dropdown kept the continent
  filter (getValue reads the selected option) but labeled the
  breadcrumb "All continents".

## Fix
Render the trigger label server-side from active_continent, falling
back to the same "globe + All continents" text as the default option's
data-label so the initial state matches what the clear button restores.

## How it was found
Section-2 re-review of the custom dropdown component: compared the
server-rendered selected option against the server-rendered trigger
label for each cselect instance.
