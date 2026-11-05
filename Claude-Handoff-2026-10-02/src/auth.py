"""OAuth PKCE login using a fresh HTTP session, with refresh support."""
import base64
import getpass
import hashlib
from html.parser import HTMLParser
import http.cookiejar
import json
import os
from pathlib import Path
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

ISSUER = os.environ.get('MODUS_ISSUER', 'https://auth.grxdiscovery.link/realms/glucorx')
CLIENT = 'modus-frontend'
REDIRECT = os.environ.get('MODUS_REDIRECT', 'https://frontend.grxdiscovery.link/')
TOKEN_FILE = Path(__file__).resolve().parents[1] / '.secrets/tokens.json'
UA = 'curl/8.0'


class LoginForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form' and a.get('id') == 'kc-form-login':
            self.action = a.get('action')
        if tag == 'input' and a.get('type') == 'hidden' and a.get('name'):
            self.inputs[a['name']] = a.get('value', '')


def parse_login_form(html):
    """Return the login action and fields from classic or Keycloakify themes."""
    form = LoginForm()
    form.feed(html)
    if form.action:
        return form.action, form.inputs
    match = re.search(r'"loginAction"\s*:\s*("(?:\\.|[^"\\])*")', html)
    if match:
        return json.loads(match.group(1)), {}
    return None, {}


class RedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if newurl.startswith(REDIRECT):
            raise urllib.error.HTTPError(newurl, code, 'OAuth callback', headers, fp)
        if urllib.parse.urlparse(newurl).netloc != urllib.parse.urlparse(ISSUER).netloc:
            raise RuntimeError('Unexpected authentication redirect host')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def token_request(fields):
    request = urllib.request.Request(ISSUER + '/protocol/openid-connect/token',
        data=urllib.parse.urlencode(fields).encode(),
        headers={'User-Agent': UA, 'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'OAuth token exchange failed: HTTP {error.code}') from None
    data['expires_at'] = time.time() + data['expires_in']
    TOKEN_FILE.parent.mkdir(exist_ok=True)
    temp = TOKEN_FILE.with_suffix('.tmp')
    temp.write_text(json.dumps(data), encoding='utf-8')
    temp.replace(TOKEN_FILE)
    return data


def login(username, password):
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    state = secrets.token_urlsafe(24)
    params = {'client_id': CLIENT, 'redirect_uri': REDIRECT, 'response_type': 'code',
              'scope': 'openid', 'state': state, 'code_challenge': challenge,
              'code_challenge_method': 'S256', 'response_mode': 'query'}
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), RedirectHandler())
    opener.addheaders = [('User-Agent', UA)]
    with opener.open(ISSUER + '/protocol/openid-connect/auth?' + urllib.parse.urlencode(params), timeout=30) as response:
        action, inputs = parse_login_form(response.read().decode())
    if not action or urllib.parse.urlparse(action).netloc != urllib.parse.urlparse(ISSUER).netloc:
        raise RuntimeError('Expected Keycloak login form was not returned')
    fields = dict(inputs, username=username, password=password)
    try:
        with opener.open(action, data=urllib.parse.urlencode(fields).encode(), timeout=30) as response:
            response.read()
        raise RuntimeError('Login requires additional action or credentials were rejected')
    except urllib.error.HTTPError as response:
        if response.code not in (302, 303) or not response.url.startswith(REDIRECT):
            raise RuntimeError(f'Login failed: HTTP {response.code}') from None
        query = urllib.parse.parse_qs(urllib.parse.urlparse(response.url).query)
    if query.get('state') != [state] or not query.get('code'):
        raise RuntimeError('OAuth callback state/code validation failed')
    return token_request({'grant_type': 'authorization_code', 'client_id': CLIENT,
                          'redirect_uri': REDIRECT, 'code': query['code'][0], 'code_verifier': verifier})


def access_token():
    data = json.loads(TOKEN_FILE.read_text(encoding='utf-8'))
    if data['expires_at'] < time.time() + 45:
        data = token_request({'grant_type': 'refresh_token', 'client_id': CLIENT,
                              'refresh_token': data['refresh_token']})
    return data['access_token']


if __name__ == '__main__':
    login(input('QA email: '), getpass.getpass('QA password: '))
    print('QA login completed. Tokens stored locally in ignored .secrets directory.')
