"""Tests for the packages list's random ordering.

The order is shuffled in Python against a seed stored in the session,
rather than via SQL ORDER BY RANDOM() — the latter reshuffles on every
single query, so a page 2 fetched independently from page 1 would show
an unrelated random slice: packages could repeat across pages or never
appear at all. These tests guard against that regression.
"""
from models.package import TourPackage


def _make_package(db, **overrides):
    defaults = dict(
        title="Test Package",
        description="A test tour package",
        destination="Test Destination",
        duration_days=5,
        price=10000.00,
        currency="PHP",
        is_active=True,
        package_type="domestic",
    )
    defaults.update(overrides)
    package = TourPackage(**defaults)
    db.session.add(package)
    db.session.commit()
    return package


class TestPackageListCoverageAcrossPages:
    def test_all_packages_appear_exactly_once_across_paginated_pages(self, app, client):
        from app import db

        titles = [f"Package {i}" for i in range(20)]
        for title in titles:
            _make_package(db, title=title)

        seen = set()
        # Page 1 is a normal load; every page after that is how the site's
        # own pagination links actually fetch subsequent pages (AJAX).
        response = client.get("/packages/")
        page_html = response.get_data(as_text=True)
        seen |= {t for t in titles if t in page_html}

        for page_num in range(2, 6):
            response = client.get(f"/packages/?page={page_num}", headers={"X-Requested-With": "XMLHttpRequest"})
            page_html = response.get_data(as_text=True)
            found = {t for t in titles if t in page_html}
            if not found:
                break
            seen |= found

        assert seen == set(titles)


class TestShuffleSeedStability:
    def test_seed_persists_across_ajax_pagination_requests(self, app, client):
        from app import db

        for i in range(15):
            _make_package(db, title=f"Package {i}")

        client.get("/packages/")
        with client.session_transaction() as sess:
            first_load_seed = sess.get("packages_shuffle_seed")
        assert first_load_seed is not None

        client.get("/packages/?page=2", headers={"X-Requested-With": "XMLHttpRequest"})
        with client.session_transaction() as sess:
            ajax_seed = sess.get("packages_shuffle_seed")

        assert ajax_seed == first_load_seed

    def test_seed_reshuffles_on_fresh_full_page_visit(self, app, client):
        from app import db

        for i in range(15):
            _make_package(db, title=f"Package {i}")

        client.get("/packages/")
        with client.session_transaction() as sess:
            first_seed = sess.get("packages_shuffle_seed")

        client.get("/packages/")
        with client.session_transaction() as sess:
            second_seed = sess.get("packages_shuffle_seed")

        assert first_seed != second_seed