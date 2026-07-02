"""OAuth client registration for Google and Facebook sign-in.

Kept in its own module (mirrors email_verification_service.py,
backup_service.py) rather than bolted directly into app.py, since
create_app() is already long.
"""
import os
from authlib.integrations.flask_client import OAuth

oauth = OAuth()


def init_oauth(app):
    """Register the Google and Facebook OAuth clients on the app.

    Call this once from create_app(), after db/login_manager/etc. are
    initialized. Missing credentials are tolerated (buttons will still
    render — the callback route just fails loudly with a clear log line
    rather than crashing app startup) so local dev without OAuth set up
    doesn't break.
    """
    oauth.init_app(app)

    if os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=os.getenv('GOOGLE_CLIENT_ID'),
            client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'},
        )
    else:
        app.logger.warning('GOOGLE_CLIENT_ID/SECRET not set — Google sign-in disabled')

