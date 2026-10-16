"""Authenticated stravalib client with a browser OAuth flow and a cached token."""

import json
import os
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from stravalib import Client

TOKEN_FILE = Path.home() / ".config" / "strava" / "token.json"
REDIRECT_PORT = 8000


def _authorize(client: Client, client_id: int) -> str:
    """Runs the browser OAuth flow and returns the authorization code."""
    codes = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            codes.extend(query.get("code", []))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorized. You can close this tab.")

        def log_message(self, *args):
            pass

    url = client.authorization_url(
        client_id=client_id,
        redirect_uri=f"http://localhost:{REDIRECT_PORT}/callback",
        scope=["activity:read_all"],
    )
    print(f"Opening browser for Strava authorization: {url}")
    webbrowser.open(url)
    with HTTPServer(("localhost", REDIRECT_PORT), Handler) as server:
        server.handle_request()
    if not codes:
        raise RuntimeError("authorization denied or no code returned")
    return codes[0]


def client() -> Client:
    """Returns a client authorized via STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET.

    The token is refreshed automatically by stravalib, which reads the same env vars.
    """
    client_id = int(os.environ["STRAVA_CLIENT_ID"])
    client_secret = os.environ["STRAVA_CLIENT_SECRET"]
    c = Client()

    if not TOKEN_FILE.exists():
        token = c.exchange_code_for_token(client_id, client_secret, _authorize(c, client_id))
    else:
        token = json.loads(TOKEN_FILE.read_text())
        if token["expires_at"] < time.time() + 3600:
            token = c.refresh_access_token(client_id, client_secret, token["refresh_token"])

    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(token))
    TOKEN_FILE.chmod(0o600)

    c.access_token = token["access_token"]
    c.refresh_token = token["refresh_token"]
    c.token_expires = token["expires_at"]
    return c
