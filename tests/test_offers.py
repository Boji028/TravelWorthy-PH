"""Tests for the Offers feature: public pages, group inquiries and admin CRUD."""
from datetime import date, timedelta
from models.offer import Offer
from models.inquiry import Inquiry


def _make_offer(db, **overrides):
    defaults = dict(title="Team Building in Batangas", category="Team Building", is_active=True)
    defaults.update(overrides)
    offer = Offer(**defaults)
    db.session.add(offer)
    db.session.commit()
    return offer


def _inquiry_form(**overrides):
    start = date.today() + timedelta(days=30)
    data = dict(
        name="Juan Dela Cruz",
        email="juan@example.com",
        contact_number="09171234567",
        organization="ABC Corporation",
        num_adults="40",
        travel_date_from=start.isoformat(),
        travel_date_to=(start + timedelta(days=2)).isoformat(),
        special_requests="Beach venue please",
        privacy_consent="y",
    )
    data.update(overrides)
    return data


class TestPublicOffers:
    def test_list_shows_only_active(self, app, client):
        from app import db

        _make_offer(db, title="Visible Offer")
        _make_offer(db, title="Hidden Offer", is_active=False)
        html = client.get("/offers/").get_data(as_text=True)
        assert "Visible Offer" in html
        assert "Hidden Offer" not in html

    def test_empty_list_renders(self, app, client):
        assert client.get("/offers/").status_code == 200

    def test_detail_renders(self, app, client):
        from app import db

        offer = _make_offer(db, description="- Games\n- Lunch", price=4500, min_pax=20)
        html = client.get(f"/offers/{offer.id}").get_data(as_text=True)
        assert "Team Building in Batangas" in html
        assert "4,500" in html
        assert "Min. 20" in html

    def test_inactive_detail_404(self, app, client):
        from app import db

        offer = _make_offer(db, is_active=False)
        assert client.get(f"/offers/{offer.id}").status_code == 404

    def test_nav_has_offers_link(self, app, client):
        assert 'href="/offers/"' in client.get("/").get_data(as_text=True)


class TestOfferInquiry:
    def test_valid_post_creates_tagged_inquiry(self, app, client):
        from app import db

        offer = _make_offer(db)
        response = client.post(f"/offers/{offer.id}", data=_inquiry_form())
        assert response.status_code == 302
        inquiry = Inquiry.query.one()
        assert inquiry.destination == offer.title
        assert inquiry.num_adults == 40
        assert inquiry.inquiry_type == "offer"
        assert inquiry.special_requests.startswith("[FOR OFFER]")
        assert "Organization: ABC Corporation" in inquiry.special_requests

    def test_group_over_100_allowed(self, app, client):
        from app import db

        offer = _make_offer(db)
        client.post(f"/offers/{offer.id}", data=_inquiry_form(num_adults="250"))
        assert Inquiry.query.one().num_adults == 250

    def test_invalid_post_shows_errors(self, app, client):
        from app import db

        offer = _make_offer(db)
        response = client.post(f"/offers/{offer.id}", data=_inquiry_form(name="Juan"))
        assert response.status_code == 200
        assert Inquiry.query.count() == 0

    def test_missing_consent_rejected(self, app, client):
        from app import db

        offer = _make_offer(db)
        data = _inquiry_form()
        data.pop("privacy_consent")
        client.post(f"/offers/{offer.id}", data=data)
        assert Inquiry.query.count() == 0

    def test_admin_type_filter_finds_offer_inquiry(self, app, client, admin_client):
        from app import db

        offer = _make_offer(db, title="Field Trip Deal")
        client.post(f"/offers/{offer.id}", data=_inquiry_form())
        html = admin_client.get("/admin/inquiries?type=offer").get_data(as_text=True)
        assert 'badge-type offer' in html
        html = admin_client.get("/admin/inquiries?type=trip").get_data(as_text=True)
        assert 'badge-type offer' not in html


class TestAdminOffers:
    def test_requires_login(self, client):
        assert client.get("/admin/offers").status_code in (302, 401, 403)

    def test_rejects_non_admin(self, app, authenticated_client):
        authenticated_client.post("/admin/offers/add", data={"title": "X", "category": "Other"})
        assert Offer.query.count() == 0

    def test_list_renders(self, app, admin_client):
        from app import db

        _make_offer(db)
        assert "Team Building in Batangas" in admin_client.get("/admin/offers").get_data(as_text=True)

    def test_add_creates_offer(self, app, admin_client):
        response = admin_client.post(
            "/admin/offers/add",
            data={
                "title": "Corporate Incentive Trip",
                "category": "Corporate Incentive",
                "price": "12000",
                "min_pax": "15",
                "image_url": "https://res.cloudinary.com/test/image/upload/v1/travelworthyph/offer/a.jpg",
                "is_active": "on",
            },
        )
        assert response.status_code == 302
        offer = Offer.query.one()
        assert offer.min_pax == 15
        assert offer.image.startswith("https://")
        assert offer.is_active

    def test_add_rejects_bad_category(self, app, admin_client):
        admin_client.post("/admin/offers/add", data={"title": "X", "category": "Hacking"})
        assert Offer.query.count() == 0

    def test_add_rejects_negative_price(self, app, admin_client):
        admin_client.post("/admin/offers/add", data={"title": "X", "category": "Other", "price": "-5"})
        assert Offer.query.count() == 0

    def test_edit_updates_offer(self, app, admin_client):
        from app import db

        offer = _make_offer(db)
        admin_client.post(f"/admin/offers/edit/{offer.id}", data={"title": "Renamed", "category": "Events"})
        db.session.refresh(offer)
        assert offer.title == "Renamed"
        assert offer.category == "Events"
        assert offer.is_active is False

    def test_toggle_active(self, app, admin_client):
        from app import db

        offer = _make_offer(db)
        response = admin_client.post(f"/admin/offers/toggle-active/{offer.id}")
        assert response.get_json()["is_active"] is False

    def test_delete(self, app, admin_client):
        from app import db

        offer = _make_offer(db)
        admin_client.post(f"/admin/offers/delete/{offer.id}")
        assert Offer.query.count() == 0
