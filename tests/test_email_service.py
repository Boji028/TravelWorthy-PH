"""Tests for email_service._send() header-injection guard."""
import email_service


def test_send_strips_crlf_from_subject(app, monkeypatch):
    """Regression test: _send() must sanitize the subject before handing it
    to Message, since callers build subjects from user-controlled fields
    (e.g. Inquiry.destination) with no CRLF restriction in their own
    validators. A crafted value like "Palawan\\r\\nBcc: evil@example.com"
    must not reach the outgoing Message with the CRLF intact."""
    app.config["MAIL_USERNAME"] = "fake@gmail.com"
    sent = {}

    def _capture(msg):
        sent["subject"] = msg.subject

    monkeypatch.setattr(email_service.mail, "send", _capture)

    email_service._send(
        subject="We received your Palawan\r\nBcc: evil@example.com inquiry!",
        recipients=["juan@example.com"],
        body="body",
    )

    assert "\r" not in sent["subject"]
    assert "\n" not in sent["subject"]
    assert "Bcc:" in sent["subject"]  # content preserved, just no longer a header break
