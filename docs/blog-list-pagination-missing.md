# Blog list: posts beyond page 1 were unreachable

## What was wrong
`blog.blog_list` paginates at 10 posts per page, but only passed
`posts.items` to the template — never the pagination object — and
`templates/blog/list.html` contained no pagination controls at all. With
more than 10 published stories, older posts simply could not be reached
from the public site (only via direct `?page=2` URLs nobody is shown, or
the sitemap).

Pytest missed it because tests assert page-1 content renders, and the
template renders fine — the bug is the absence of navigation.

## Fix
- `routes/blog.py` — pass `pagination=posts` (the paginate object) to the
  template alongside the existing `posts=posts.items`.
- `templates/blog/list.html` — added a centered pagination bar after the
  stories grid, reusing the existing `.category-bar` pill styling (which
  already has an `.active` state) and the same `iter_pages()` pattern as
  `templates/packages/_pagination.html`. The active category filter is
  preserved across page links (`category=active_category or none` so no
  empty `?category=` param is emitted).
