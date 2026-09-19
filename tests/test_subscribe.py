"""Tests for the public Subscribe route (/subscribe) and Subscriber model."""
from models.subscriber import Subscriber


class TestSubscribe:
    def test_valid_signup_creates_subscriber_row(self, app, client):
        from app import db

        response = client.post("/subscribe", data={"name": "Jane Doe", "email": "jane@example.com"})
        assert response.status_code == 200
        subscriber = db.session.query(Subscriber).filter_by(email="jane@example.com").first()
        assert subscriber is not None
        assert subscriber.name == "Jane Doe"

    def test_valid_signup_returns_success_json(self, client):
        response = client.post("/subscribe", data={"name": "Jane Doe", "email": "jane@example.com"})
        data = response.get_json()
        assert data["success"] is True

    def test_duplicate_email_returns_success_without_duplicate_row(self, app, client):
        from app import db

        client.post("/subscribe", data={"name": "Jane Doe", "email": "dupe@example.com"})
        response = client.post("/subscribe", data={"name": "Jane Again", "email": "dupe@example.com"})

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert Subscriber.query.filter_by(email="dupe@example.com").count() == 1

    def test_invalid_email_format_rejected(self, app, client):
        response = client.post("/subscribe", data={"name": "Bad Email", "email": "not-an-email"})
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert Subscriber.query.filter_by(name="Bad Email").first() is None

    def test_missing_name_rejected(self, app, client):
        response = client.post("/subscribe", data={"name": "", "email": "noname@example.com"})
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert Subscriber.query.filter_by(email="noname@example.com").first() is None

    def test_repeated_signups_get_rate_limited(self, client):
        """Same class of check as the login/forgot-password rate limits —
        5 per hour, keyed by the submitted email, so the 6th request for
        the same address should be blocked."""
        for _ in range(5):
            response = client.post("/subscribe", data={"name": "Rate Test", "email": "ratelimited@example.com"})
            assert response.status_code == 200

        response = client.post("/subscribe", data={"name": "Rate Test", "email": "ratelimited@example.com"})
        assert response.status_code == 429
