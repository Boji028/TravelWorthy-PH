"""Tests for the mobile filter sheet markup on the packages list page.

The sheet replaced an inline-expanding filter bar that looked cluttered on
small screens (wrapping region pills, an inline country flyout pushing
content around). These tests just check the sheet renders with the right
active states and that every continent's country panel is present in the
DOM (needed so switching regions client-side doesn't require another
request).
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
        assert 'class="mobile-chip active"' in page
        assert 'data-continent-id=""' in page

    def test_active_continent_and_country_are_marked_active_in_sheet(self, app, client):
        from app import db

        oceania = _make_continent(db, "Oceania")
        australia = _make_country(db, oceania, "Australia")
        _make_package(db, australia, "Sydney Tour")

        response = client.get(f"/packages/?continent_id={oceania.id}&country_id={australia.id}")
        page = response.get_data(as_text=True)

        assert f'data-continent-id="{oceania.id}" data-label="Oceania"' in page
        assert f'data-continent-panel="{oceania.id}"' in page
        assert f'class="mobile-country-grid open"\n            data-continent-panel="{oceania.id}"' in page
        assert f'data-country-id="{australia.id}" data-label="Oceania → Australia"' in page

    def test_every_continent_gets_its_own_country_panel(self, app, client):
        """All continents render a panel (not just the active one) so the
        sheet can switch regions client-side without another request."""
        from app import db

        oceania = _make_continent(db, "Oceania")
        _make_country(db, oceania, "Australia")
        asia = _make_continent(db, "Asia")
        _make_country(db, asia, "Japan")

        response = client.get(f"/packages/?continent_id={oceania.id}")
        page = response.get_data(as_text=True)

        assert f'data-continent-panel="{oceania.id}"' in page
        assert f'data-continent-panel="{asia.id}"' in page
        assert "Japan" in page

    def test_mobile_type_segments_reflect_active_package_type(self, app, client):
        response = client.get("/packages/?package_type=domestic")
        page = response.get_data(as_text=True)
        assert 'class="mobile-seg active" data-type="domestic"' in page
        assert 'class="mobile-seg " data-type=""' in page
