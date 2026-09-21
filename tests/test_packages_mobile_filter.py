"""Tests for the continent/country filter markup on the packages list page.

The mobile filter sheet was removed: mobile now shows the same
continent icon badges and country pill row as desktop, scrolling
sideways instead of collapsing into a bottom sheet with dropdowns.
These tests cover the markup both breakpoints share.
"""
from models.package import TourPackage
from models.continent import Continent
from models.country import Country


def _make_continent(db, name, **overrides):
    defaults = dict(name=name, is_active=True)
    defaults.update(overrides)
    continent = Continent(**defaults)
    db.session.add(continent)
    db.session.commit()
    return continent


def _make_country(db, continent, name, **overrides):
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


class TestContinentFilter:
    def test_continent_badges_render(self, app, client):
        from app import db

        _make_continent(db, "Asia")

        response = client.get("/packages/")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'class="country-tabs-inner"' in page
        # The "All" badge plus one per continent.
        assert "images/continents/all.svg" in page
        assert "images/continents/asia.svg" in page

    def test_unknown_continent_name_falls_back_to_the_globe_icon(self, app, client):
        """A continent added in admin with no matching icon file should
        still render, using all.svg, rather than a broken image."""
        from app import db

        _make_continent(db, "Atlantis")

        page = client.get("/packages/").get_data(as_text=True)
        assert "images/continents/atlantis.svg" not in page
        assert "images/continents/all.svg" in page

    def test_every_continent_gets_its_own_country_pill_row(self, app, client):
        """Rows for all continents are rendered up front and toggled by
        JS, because AJAX filtering never re-renders the toolbar."""
        from app import db

        asia = _make_continent(db, "Asia")
        europe = _make_continent(db, "Europe")
        _make_country(db, asia, "Japan")
        _make_country(db, europe, "France")

        page = client.get("/packages/").get_data(as_text=True)
        assert f'data-continent="{asia.id}"' in page
        assert f'data-continent="{europe.id}"' in page
        assert "Japan" in page
        assert "France" in page

    def test_only_the_active_continent_row_is_visible(self, app, client):
        from app import db

        asia = _make_continent(db, "Asia")
        europe = _make_continent(db, "Europe")
        _make_country(db, asia, "Japan")
        _make_country(db, europe, "France")

        page = client.get(f"/packages/?continent_id={asia.id}").get_data(as_text=True)
        # The inactive continent's row carries the hidden attribute.
        assert f'data-continent="{europe.id}"\n      hidden' in page or f'data-continent="{europe.id}" hidden' in page

    def test_country_pills_show_package_counts(self, app, client):
        from app import db

        asia = _make_continent(db, "Asia")
        japan = _make_country(db, asia, "Japan")
        _make_package(db, japan, "Tokyo Tour")

        page = client.get("/packages/").get_data(as_text=True)
        assert 'class="cp-count"' in page

    def test_the_removed_mobile_filter_sheet_is_gone(self, app, client):
        from app import db

        _make_continent(db, "Asia")

        page = client.get("/packages/").get_data(as_text=True)
        assert "mobileSheetOverlay" not in page
        assert "mobileFilterToggle" not in page
