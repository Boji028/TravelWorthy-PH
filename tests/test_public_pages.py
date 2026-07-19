"""Tests for public-facing pages and user routes."""
from datetime import date, timedelta
from models.inquiry import Inquiry
from models.testimonial import Testimonial


def _make_inquiry(db, user_id=None, **overrides):
    today = date.today()
    defaults = dict(
        name="Test Customer",
        email="customer@example.com",
        contact_number="+639171234567",
        destination="Palawan",
        travel_date_from=today + timedelta(days=10),
        travel_date_to=today + timedelta(days=14),
        num_adults=2,
        status="new",
        user_id=user_id,
    )
    defaults.update(overrides)
    inquiry = Inquiry(**defaults)
    db.session.add(inquiry)
    db.session.commit()
    return inquiry


class TestContactPage:
    """Contact Us is now a plain reach-us-details page — the message
    form, ContactMessage model, and admin Contact Messages panel were
    all removed at the boss's request."""

    def test_contact_page_renders_with_details(self, client):
        response = client.get("/contact")
        assert response.status_code == 200
        assert b"+639178247128" in response.data
        assert b"travelworthyph@gmail.com" in response.data

    def test_contact_page_has_no_message_form(self, client):
        response = client.get("/contact")
        assert b"Send Us a Message" not in response.data
        assert b'name="message"' not in response.data

    def test_contact_page_only_accepts_get(self, client):
        response = client.post("/contact", data={"name": "Juan"})
        assert response.status_code == 405


class TestTrackInquiry:
    def test_valid_reference_renders_page(self, app, client):
        from app import db

        inquiry = _make_inquiry(db)
        response = client.get(f"/inquiry/{inquiry.reference_number}")
        assert response.status_code == 200

    def test_invalid_reference_returns_404(self, client):
        response = client.get("/inquiry/INQ-DOESNOTEXIST")
        assert response.status_code == 404

    def test_reference_lookup_is_case_insensitive(self, app, client):
        from app import db

        inquiry = _make_inquiry(db)
        lower_ref = inquiry.reference_number.lower()
        response = client.get(f"/inquiry/{lower_ref}")
        assert response.status_code == 200

    def test_failed_confirmation_email_shows_a_notice(self, app, client):
        """The customer-facing half of the email-failure fix: since the
        confirmation email is sent asynchronously (after the initial
        response has already been returned), the tracking page - which
        the customer is given a link to regardless - is the one place
        that can accurately reflect whether it actually sent, by the
        time they check it."""
        from app import db

        inquiry = _make_inquiry(db, confirmation_email_failed=True)
        response = client.get(f"/inquiry/{inquiry.reference_number}")
        assert b"weren't able to send a confirmation email" in response.data

    def test_successful_confirmation_email_shows_no_notice(self, app, client):
        from app import db

        inquiry = _make_inquiry(db, confirmation_email_failed=False)
        response = client.get(f"/inquiry/{inquiry.reference_number}")
        assert b"weren't able to send a confirmation email" not in response.data


class TestMyInquiries:
    def test_requires_login(self, client):
        response = client.get("/my-inquiries")
        assert response.status_code in (302, 401, 403)

    def test_shows_only_own_inquiries(self, app, authenticated_client, test_user):
        from app import db

        own = _make_inquiry(db, user_id=test_user.id, email="own@example.com")
        other = _make_inquiry(db, user_id=None, email="other@example.com")
        response = authenticated_client.get("/my-inquiries")
        assert response.status_code == 200
        assert own.reference_number.encode() in response.data
        assert other.reference_number.encode() not in response.data

    def test_renders_empty_state(self, app, authenticated_client):
        response = authenticated_client.get("/my-inquiries")
        assert response.status_code == 200


class TestReviewsPage:
    def test_renders_with_no_testimonials(self, client):
        response = client.get("/reviews")
        assert response.status_code == 200

    def test_renders_with_testimonials(self, app, client, test_user):
        from app import db

        db.session.add(Testimonial(user_id=test_user.id, message="Great!", rating=5))
        db.session.commit()
        response = client.get("/reviews")
        assert response.status_code == 200

    def test_pagination_param_accepted(self, client):
        response = client.get("/reviews?page=1")
        assert response.status_code == 200


class TestHomePage:
    def test_home_renders(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_about_renders(self, client):
        response = client.get("/about")
        assert response.status_code == 200
