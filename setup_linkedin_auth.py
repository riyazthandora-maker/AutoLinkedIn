"""
One-time LinkedIn OAuth 2.0 setup helper.

Run locally:
    python setup_linkedin_auth.py

Prerequisites:
    1. Create a LinkedIn Developer App at https://developer.linkedin.com/
    2. Under "Auth", add redirect URI: http://localhost:8080/callback
    3. Add product "Share on LinkedIn" to get w_member_social scope
    4. Copy your Client ID and Client Secret below (or set as env vars)

After running, copy the printed access token into GitHub Secrets as LINKEDIN_ACCESS_TOKEN.
Token expires in 60 days. Refresh token expires in 365 days — re-run this script annually.
"""

import os
import sys
import urllib.parse
import urllib.request
import webbrowser
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer


CLIENT_ID = os.environ.get("LINKEDIN_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "openid profile w_member_social"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

_auth_code: str = ""
_state: str = secrets.token_urlsafe(16)


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "error" in params:
            error = params["error"][0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"OAuth error: {error}".encode())
            return

        returned_state = params.get("state", [""])[0]
        if returned_state != _state:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"State mismatch - possible CSRF. Try again.")
            return

        _auth_code = params.get("code", [""])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Authorization successful! You can close this tab.</h2>")

    def log_message(self, format, *args):
        pass


def exchange_code_for_token(code: str) -> dict:
    import json

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET as environment variables, then re-run.")
        print("  $env:LINKEDIN_CLIENT_ID='your_client_id'")
        print("  $env:LINKEDIN_CLIENT_SECRET='your_client_secret'")
        sys.exit(1)

    auth_params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "state": _state,
    })
    full_auth_url = f"{AUTH_URL}?{auth_params}"

    print("Opening LinkedIn authorization in your browser...")
    print(f"If it doesn't open, visit:\n  {full_auth_url}\n")
    webbrowser.open(full_auth_url)

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    print("Waiting for callback on http://localhost:8080/callback ...")
    server.handle_request()

    if not _auth_code:
        print("No auth code received. Exiting.")
        sys.exit(1)

    print("Exchanging authorization code for access token...")
    tokens = exchange_code_for_token(_auth_code)

    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "N/A")
    expires_in = tokens.get("expires_in", "unknown")

    print("\n" + "=" * 60)
    print("SUCCESS — copy the access token below into GitHub Secrets")
    print("=" * 60)
    print(f"\nLINKEDIN_ACCESS_TOKEN:\n{access_token}")
    print(f"\nRefresh token (store safely, valid ~365 days):\n{refresh_token}")
    print(f"\nAccess token expires in: {expires_in} seconds (~{int(expires_in)//86400} days)")
    print("\nAdd LINKEDIN_ACCESS_TOKEN to: GitHub repo -> Settings -> Secrets -> Actions")


if __name__ == "__main__":
    main()
