"""Tests for public inquiry submission routes (plan_my_trip, inquire_package)."""
from datetime import date, timedelta
from models.inquiry import Inquiry
from models.package import TourPackage


def _future(days):
    return (date.today() + timedelta(days=days)).isoformat()


def _valid_form(**overrides):
    data = dict(
        name='Juan dela Cruz',
        email='juan@example.com',
        contact_number='+639171234567',
        destination='Palawan',
        travel_date_from=_future(10),
        travel_date_to=_future(14),
        num_adults=2,
        num_children=0,
        num_infants=0,
    )
    data.update(overrides)
    return data


def _make_package(db, **overrides):
    defaults = dict(
        title='Palawan Tour',
        description='A beautiful tour',
        destination='Palawan',
        duration_days=5,
        price=9999.00,
        currency='PHP',
        is_active=True,
    )
    defaults.update(overrides)
    pkg = TourPackage(**defaults)
    db.session.add(pkg)
    db.session.commit()
    return pkg


class TestInquiryEmailIsAsync:
    """Guards the fix for inquiries taking ~5s to submit — the old code sent
    both notification emails synchronously before returning the redirect.
    Each simulated slow send below stands in for one real SMTP round trip."""

    def test_plan_my_trip_does_not_block_on_slow_email(self, app, client, monkeypatch):
        import time
        import email_service
        app.config['MAIL_USERNAME'] = 'fake@gmail.com'  # so _send() doesn't skip early

        monkeypatch.setattr(email_service.mail, 'send', lambda msg: time.sleep(0.5))

        start = time.perf_counter()
        response = client.post('/bookings/plan-my-trip', data=_valid_form())
        elapsed = time.perf_counter() - start

        assert response.status_code == 302
        assert elapsed < 0.3  # well under the simulated 0.5s-per-email send time
        time.sleep(0.6)  # let the background thread finish before teardown drops the DB


class TestPlanMyTrip:
    def test_get_renders_form(self, client):
        response = client.get('/bookings/plan-my-trip')
        assert response.status_code == 200

    def test_valid_post_creates_inquiry_and_redirects(self, app, client):
        from app import db
        response = client.post('/bookings/plan-my-trip', data=_valid_form(), follow_redirects=False)
        assert response.status_code == 302
        assert Inquiry.query.count() == 1
        inquiry = Inquiry.query.first()
        assert inquiry.destination == 'Palawan'
        assert inquiry.user_id is None

    def test_reference_number_is_generated(self, app, client):
        from app import db
        client.post('/bookings/plan-my-trip', data=_valid_form())
        inquiry = Inquiry.query.first()
        assert inquiry.reference_number.startswith('INQ-')

    def test_missing_name_fails_validation(self, app, client):
        from app import db
        client.post('/bookings/plan-my-trip', data=_valid_form(name=''))
        assert Inquiry.query.count() == 0

    def test_missing_email_fails_validation(self, app, client):
        from app import db
        client.post('/bookings/plan-my-trip', data=_valid_form(email=''))
        assert Inquiry.query.count() == 0

    def test_invalid_email_fails_validation(self, app, client):
        from app import db
        client.post('/bookings/plan-my-trip', data=_valid_form(email='not-an-email'))
        assert Inquiry.query.count() == 0

    def test_return_before_departure_fails_validation(self, app, client):
        from app import db
        client.post('/bookings/plan-my-trip', data=_valid_form(
            travel_date_from=_future(14),
            travel_date_to=_future(10),
        ))
        assert Inquiry.query.count() == 0

    def test_past_departure_date_fails_validation(self, app, client):
        from app import db
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        client.post('/bookings/plan-my-trip', data=_valid_form(
            travel_date_from=yesterday,
            travel_date_to=_future(5),
        ))
        assert Inquiry.query.count() == 0

    def test_zero_adults_fails_validation(self, app, client):
        from app import db
        client.post('/bookings/plan-my-trip', data=_valid_form(num_adults=0))
        assert Inquiry.query.count() == 0

    def test_optional_children_and_infants_default_to_zero(self, app, client):
        from app import db
        data = _valid_form()
        data.pop('num_children')
        data.pop('num_infants')
        client.post('/bookings/plan-my-trip', data=data)
        inquiry = Inquiry.query.first()
        if inquiry:
            assert inquiry.num_children == 0
            assert inquiry.num_infants == 0

    def test_logged_in_user_inquiry_linked_to_account(self, app, authenticated_client):
        from app import db
        authenticated_client.post('/bookings/plan-my-trip', data=_valid_form())
        inquiry = Inquiry.query.first()
        assert inquiry is not None
        assert inquiry.user_id is not None

    def test_redirect_goes_to_tracking_page(self, app, client):
        from app import db
        response = client.post('/bookings/plan-my-trip', data=_valid_form(), follow_redirects=False)
        assert response.status_code == 302
        inquiry = Inquiry.query.first()
        assert inquiry.reference_number in response.headers['Location']


class TestInquirePackage:
    def test_get_renders_form(self, app, client):
        from app import db
        pkg = _make_package(db)
        response = client.get(f'/bookings/inquire/{pkg.id}')
        assert response.status_code == 200

    def test_nonexistent_package_redirects(self, client):
        response = client.get('/bookings/inquire/99999', follow_redirects=False)
        assert response.status_code in (302, 404)

    def test_valid_post_creates_inquiry_linked_to_package(self, app, client):
        from app import db
        pkg = _make_package(db)
        client.post(f'/bookings/inquire/{pkg.id}', data=_valid_form())
        inquiry = Inquiry.query.first()
        assert inquiry is not None
        assert inquiry.package_id == pkg.id

    def test_missing_required_field_does_not_create_inquiry(self, app, client):
        from app import db
        pkg = _make_package(db)
        client.post(f'/bookings/inquire/{pkg.id}', data=_valid_form(name=''))
        assert Inquiry.query.count() == 0

    def test_email_lowercased_on_save(self, app, client):
        from app import db
        pkg = _make_package(db)
        client.post(f'/bookings/inquire/{pkg.id}', data=_valid_form(email='JUAN@EXAMPLE.COM'))
        inquiry = Inquiry.query.first()
        assert inquiry is not None
        assert inquiry.email == 'juan@example.com'
