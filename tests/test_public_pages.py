"""Tests for public-facing pages and user routes."""
from datetime import date, timedelta
from models.inquiry import Inquiry
from models.contact import ContactMessage
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


class TestContactRoute:
    def test_get_renders_form(self, client):
        response = client.get("/contact")
        assert response.status_code == 200

    def test_valid_post_saves_message(self, app, client):
        from app import db

        client.post(
            "/contact",
            data={
                "name": "Juan Dela Cruz",
                "email": "juan@example.com",
                "subject": "Hello there",
                "message": "I have a question about your tours.",
            },
        )
        assert ContactMessage.query.count() == 1

    def test_missing_name_does_not_save(self, app, client):
        from app import db

        client.post(
            "/contact",
            data={
                "name": "",
                "email": "juan@example.com",
                "subject": "Hello",
                "message": "A question.",
            },
        )
        assert ContactMessage.query.count() == 0

    def test_missing_email_does_not_save(self, app, client):
        from app import db

        client.post(
            "/contact",
            data={
                "name": "Juan",
                "email": "",
                "subject": "Hello",
                "message": "A question.",
            },
        )
        assert ContactMessage.query.count() == 0

    def test_short_subject_does_not_save(self, app, client):
        from app import db

        client.post(
            "/contact",
            data={
                "name": "Juan",
                "email": "juan@example.com",
                "subject": "H",
                "message": "A question.",
            },
        )
        assert ContactMessage.query.count() == 0

    def test_valid_post_redirects(self, app, client):
        response = client.post(
            "/contact",
            data={
                "name": "Juan Dela Cruz",
                "email": "juan@example.com",
                "subject": "Hello there",
                "message": "I have a question about your tours.",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302

    def test_logged_in_user_linked_to_message(self, app, authenticated_client, test_user):
        from app import db

        authenticated_client.post(
            "/contact",
            data={
                "name": "Juan Dela Cruz",
                "email": "juan@example.com",
                "subject": "Hello there",
                "message": "I have a question about your tours.",
            },
        )
        msg = ContactMessage.query.first()
        assert msg is not None
        assert msg.user_id == test_user.id

    def test_single_word_name_shows_error_message(self, app, client):
        """Regression test - contact.html only ever displayed errors for
        the message field; name/email/subject failures used to just
        redisplay a blank form with no explanation, identical to the bug
        already fixed on the inquiry forms."""
        response = client.post(
            "/contact",
            data={
                "name": "Juan",
                "email": "juan@example.com",
                "subject": "Question about a package",
                "message": "A question.",
            },
        )
        assert response.status_code == 200
        assert b"Please enter your first and last name" in response.data

    def test_invalid_submission_preserves_entered_values(self, app, client):
        """Regression test - previously entered values used to be wiped on
        a failed submission."""
        response = client.post(
            "/contact",
            data={
                "name": "Juan",
                "email": "juan@example.com",
                "subject": "Question about a package",
                "message": "A question about the Palawan tour.",
            },
        )
        assert response.status_code == 200
        assert b"juan@example.com" in response.data
        assert b"Question about a package" in response.data
        assert b"A question about the Palawan tour." in response.data


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
