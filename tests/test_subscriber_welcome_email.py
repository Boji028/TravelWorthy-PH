"""Tests for the automatic subscriber welcome email and unsubscribe link.

Kept in its own file (not tests/test_subscribe.py) since that file
already exists with its own coverage of the base /subscribe route.
"""
from models.subscriber import Subscriber


class TestSubscriberWelcomeEmail:
    def test_new_subscriber_receives_welcome_email(self, app, client, monkeypatch):
        from app import mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"
        sent_messages = []
        monkeypatch.setattr(app_mail, "send", lambda msg: sent_messages.append(msg))

        client.post("/subscribe", data={"name": "Enzo Castillo", "email": "enzo@example.com"})

        assert len(sent_messages) == 1
        assert sent_messages[0].recipients == ["enzo@example.com"]
        assert "subscribed" in sent_messages[0].subject.lower()

    def test_duplicate_subscribe_does_not_resend_welcome_email(self, app, client, monkeypatch):
        from app import db, mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"
        db.session.add(Subscriber(name="Existing", email="already@example.com"))
        db.session.commit()

        sent_messages = []
        monkeypatch.setattr(app_mail, "send", lambda msg: sent_messages.append(msg))

        response = client.post("/subscribe", data={"name": "Existing", "email": "already@example.com"})

        assert response.get_json()["success"] is True
        assert len(sent_messages) == 0

    def test_welcome_email_contains_working_unsubscribe_link(self, app, client, monkeypatch):
        from app import db, mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"
        sent_messages = []
        monkeypatch.setattr(app_mail, "send", lambda msg: sent_messages.append(msg))

        client.post("/subscribe", data={"name": "Enzo Castillo", "email": "enzo2@example.com"})

        subscriber = Subscriber.query.filter_by(email="enzo2@example.com").first()
        assert subscriber.unsubscribe_token
        assert f"/unsubscribe/{subscriber.unsubscribe_token}" in sent_messages[0].body

    def test_subscribe_still_succeeds_even_if_email_sending_fails(self, app, client, monkeypatch):
        """The subscription itself is the important part - a broken mail
        server should not turn a successful signup into an error for the
        person subscribing."""
        from app import mail as app_mail

        app.config["MAIL_USERNAME"] = "test@example.com"

        def _boom(msg):
            raise RuntimeError("mail server is down")

        monkeypatch.setattr(app_mail, "send", _boom)

        response = client.post("/subscribe", data={"name": "Enzo Castillo", "email": "enzo3@example.com"})

        assert response.status_code == 200
        assert response.get_json()["success"] is True
        assert Subscriber.query.filter_by(email="enzo3@example.com").first() is not None


class TestUnsubscribe:
    def test_valid_token_removes_subscriber_and_shows_confirmation(self, app, client):
        from app import db

        subscriber = Subscriber(name="Enzo Castillo", email="unsub@example.com")
        db.session.add(subscriber)
        db.session.commit()
        token = subscriber.unsubscribe_token

        response = client.get(f"/unsubscribe/{token}", follow_redirects=True)

        assert response.status_code == 200
        assert b"unsubscribed" in response.data.lower()
        assert Subscriber.query.filter_by(email="unsub@example.com").first() is None

    def test_invalid_token_still_shows_confirmation_without_error(self, client):
        """Same response whether or not the token was ever valid, so a
        reused or guessed link can't be used to probe for real tokens."""
        response = client.get("/unsubscribe/not-a-real-token", follow_redirects=True)

        assert response.status_code == 200
        assert b"unsubscribed" in response.data.lower()

    def test_each_subscriber_gets_a_unique_token(self, app, client):
        from app import db

        s1 = Subscriber(name="A", email="a@example.com")
        s2 = Subscriber(name="B", email="b@example.com")
        db.session.add_all([s1, s2])
        db.session.commit()

        assert s1.unsubscribe_token != s2.unsubscribe_token
