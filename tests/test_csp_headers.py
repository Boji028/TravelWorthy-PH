"""Tests for security headers (Content-Security-Policy via Flask-Talisman)."""


class TestContentSecurityPolicy:
    def test_frame_src_allows_cloudinary(self, client):
        """Visa PDFs are hosted on Cloudinary and previewed in an <iframe>
        on desktop (see packages/visa.html's pdf-frame) — without Cloudinary
        listed in frame-src, the browser blocks the embed with "This
        content is blocked. Contact the site owner to fix the issue."
        """
        response = client.get("/packages/visa")
        csp = response.headers.get("Content-Security-Policy", "")
        directives = dict(part.strip().split(" ", 1) for part in csp.split(";") if part.strip())
        assert "res.cloudinary.com" in directives.get("frame-src", "")