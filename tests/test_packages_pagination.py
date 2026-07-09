"""Tests for pagination staying scoped to the active filter on the packages list page.

Regression coverage for a bug where the "Prev/Next/page number" links kept
the very first server-rendered pagination context (usually the unfiltered
"All" view). After filtering by continent via AJAX, clicking a pagination
link silently dropped the filter and showed the unfiltered package list
instead of page 2 of the filtered results.
"""
from models.package import TourPackage
from models.continent import Continent
from models.country import Country


def _make_continent(db, name="Oceania", **overrides):
    defaults = dict(name=name, is_active=True)
    defaults.update(overrides)
    continent = Continent(**defaults)
    db.session.add(continent)
    db.session.commit()
    return continent


def _make_country(db, continent, name="Australia", **overrides):
    defaults = dict(name=name, is_active=True, continent_id=continent.id)
    defaults.update(overrides)
    country = Country(**defaults)
    db.session.add(country)
    db.session.commit()
    return country


def _make_package(db, country, title, **overrides):
    defaults = dict(
        title=title,
        description="A test tour package",
        destination=title,
        duration_days=5,
        price=10000.00,
        currency="PHP",
        is_active=True,
        package_type="international",
        country_id=country.id,
    )
    defaults.update(overrides)
    package = TourPackage(**defaults)
    db.session.add(package)
    db.session.commit()
    return package


class TestPaginationScopedToFilter:
    def test_ajax_response_omits_pagination_when_filtered_results_fit_one_page(self, app, client):
        """A filter with <= per_page (9) results should show no pagination at all."""
        from app import db

        continent = _make_continent(db)
        country = _make_country(db, continent)
        for i in range(3):
            _make_package(db, country, title=f"Oceania Package {i}")

        response = client.get(
            f"/packages/?continent_id={continent.id}",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert page.count("pkg-card") == 3
        assert "country-tab" not in page  # no pagination links rendered

    def test_ajax_pagination_links_keep_the_continent_filter(self, app, client):
        """A filter with > per_page (9) results must produce page links that still carry continent_id."""
        from app import db

        continent = _make_continent(db)
        country = _make_country(db, continent)
        for i in range(11):
            _make_package(db, country, title=f"Oceania Package {i}")

        response = client.get(
            f"/packages/?continent_id={continent.id}",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert response.status_code == 200
        page = response.get_data(as_text=True)

        assert f"continent_id={continent.id}" in page
        assert 'href="/packages/?' in page

    def test_page_two_of_filtered_results_only_shows_that_continent(self, app, client):
        """Following a filtered pagination link (page=2) must not fall back to the unfiltered list."""
        from app import db

        oceania = _make_continent(db, name="Oceania")
        oceania_country = _make_country(db, oceania, name="Australia")
        for i in range(11):
            _make_package(db, oceania_country, title=f"Oceania Package {i}")

        asia = _make_continent(db, name="Asia")
        asia_country = _make_country(db, asia, name="Japan")
        _make_package(db, asia_country, title="Tokyo Adventure")

        response = client.get(f"/packages/?continent_id={oceania.id}&page=2")
        assert response.status_code == 200
        page = response.get_data(as_text=True)

        assert "Oceania Package" in page
        assert "Tokyo Adventure" not in page

    def test_full_page_render_pagination_also_keeps_filter(self, app, client):
        """The non-AJAX (full page load) pagination must also carry the active continent filter."""
        from app import db

        continent = _make_continent(db)
        country = _make_country(db, continent)
        for i in range(11):
            _make_package(db, country, title=f"Oceania Package {i}")

        response = client.get(f"/packages/?continent_id={continent.id}")
        assert response.status_code == 200
        page = response.get_data(as_text=True)

        assert f"continent_id={continent.id}" in page
