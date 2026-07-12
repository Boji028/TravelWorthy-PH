"""Tests for the mobile filter sheet markup on the packages list page.

The sheet replaced an inline-expanding filter bar that looked cluttered on
small screens. Region and country selection are two cascading <select>
dropdowns: picking a continent repopulates the country dropdown client-side
from a continentCountries JS object embedded in the page (so switching
regions doesn't require another request), rather than pre-rendering one
chip grid per continent server-side.
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


class TestMobileFilterSheet:
    def test_sheet_renders_with_no_filter_active(self, app, client):
        from app import db

        _make_continent(db, "Asia")

        response = client.get("/packages/")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert 'id="mobileSheetOverlay"' in page
        assert 'id="mobileContinentSelect"' in page
        assert 'id="mobileCountrySelect"' in page
        assert '<option value="" data-label="">' in page

    def test_active_continent_is_marked_selected_in_dropdown(self, app, client):
        from app import db

        oceania = _make_continent(db, "Oceania")
        australia = _make_country(db, oceania, "Australia")
        _make_package(db, australia, "Sydney Tour")

        response = client.get(f"/packages/?continent_id={oceania.id}&country_id={australia.id}")
        page = response.get_data(as_text=True)

        assert f'value="{oceania.id}" data-label="Oceania"' in page
        assert "selected" in page.split(f'value="{oceania.id}" data-label="Oceania"')[1].split(">")[0]
        # The active country's id is threaded into the client-side
        # populateCountrySelect() call so it can be preselected once the
        # country dropdown is populated on load.
        assert f'populateCountrySelect(continentSelect.value, "{australia.id}")' in page

    def test_every_continent_gets_an_entry_in_the_country_data(self, app, client):
        """Every continent's active countries are embedded in the
        continentCountries JS object (not just the active one), so the
        sheet can switch regions client-side without another request."""
        from app import db

        oceania = _make_continent(db, "Oceania")
        _make_country(db, oceania, "Australia")
        asia = _make_continent(db, "Asia")
        _make_country(db, asia, "Japan")

        response = client.get(f"/packages/?continent_id={oceania.id}")
        page = response.get_data(as_text=True)

        assert f'"{oceania.id}":' in page
        assert f'"{asia.id}":' in page
        assert "Australia" in page
        assert "Japan" in page

    def test_inactive_country_excluded_from_country_data(self, app, client):
        from app import db

        asia = _make_continent(db, "Asia")
        _make_country(db, asia, "Japan", is_active=True)
        _make_country(db, asia, "Hidden Country", is_active=False)

        response = client.get("/packages/")
        page = response.get_data(as_text=True)

        assert "Japan" in page
        assert "Hidden Country" not in page

    def test_mobile_type_segments_reflect_active_package_type(self, app, client):
        response = client.get("/packages/?package_type=domestic")
        page = response.get_data(as_text=True)
        assert 'class="mobile-seg active" data-type="domestic"' in page
        assert 'class="mobile-seg " data-type=""' in page
