"""Provision and refresh PRT-0392 fixtures in the GlucoRx QA environment.

This tool is intentionally locked to the QA Keycloak and Modus API hosts.  It
stores account and mailbox credentials only in .secrets/prt0392-qa.json and
never prints them.  Public outputs contain email addresses and fixture status,
but no passwords, mailbox tokens, OAuth tokens, or action links.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import getpass
import json
import math
import os
from pathlib import Path
import random
import re
import secrets
import string
import sys
import time
import uuid
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SECRET_FILE = ROOT / ".secrets" / "prt0392-qa.json"
OUTPUT_DIR = ROOT / "output" / "prt0392-qa"
STATE_FILE = OUTPUT_DIR / "seed-state.json"
REPORT_FILE = OUTPUT_DIR / "provisioning-report.json"

ISSUER = "https://keycloak.dev.platform.glucorx.co.uk/realms/glucorx"
REDIRECT = "https://frontend.grxdiscovery.link/auth/login"
CLIENT = "modus-frontend"
API_BASE = "https://modapi.grxdiscovery.link"
SERVICE = "/glucorx.modus.v1alpha2.AppService/"
MAIL_API = "https://api.mail.tm"

ALLOWED_HOSTS = {
    "keycloak.dev.platform.glucorx.co.uk",
    "frontend.grxdiscovery.link",
    "modapi.grxdiscovery.link",
    "api.mail.tm",
}

ACCOUNT_SPECS = [
    ("QA-MAIN-01", "us", "QA Main", "Account", True),
    ("QA-HISTORY-01", "us", "QA History", "Account", True),
    ("QA-NODATA-01", "uk", "QA No Data", "Account", True),
    ("QA-LOGIN-US-01", "us", "QA Login US", "Account", True),
    ("QA-RESET-01", "uk", "QA Reset", "Account", True),
    ("QA-SHARE-A-01", "uk", "QA Share A", "Account", True),
    ("QA-SHARE-B-01", "uk", "QA Share B", "Account", True),
    ("QA-UNVERIFIED-01", "uk", "QA Unverified", "Account", False),
    ("QA-FRESH-01", "uk", "QA Fresh", "Account", True),
    ("QA-EMAIL-CHANGE-01", "uk", "QA Email Change", "Account", True),
    ("QA-DELETE-01", "uk", "QA Delete", "Account", True),
    ("QA-DELETE-REPL-01", "uk", "QA Delete Replacement", "Account", True),
]

MAILBOX_ONLY = [
    "QA-EMAIL-CHANGE-01-REPLACEMENT",
    "QA-REG-REGION-UK-01",
    "QA-REG-REGION-US-01",
    "QA-REG-EMAIL-A",
    "QA-REG-EMAIL-B",
    "QA-REG-EMAIL-C",
]

NO_BACKEND_ONBOARDING = {
    "QA-RESET-01",
    "QA-FRESH-01",
    "QA-EMAIL-CHANGE-01",
}


def ensure_qa_url(url: str) -> None:
    host = (urlparse(url).hostname or "").lower()
    if host not in ALLOWED_HOSTS:
        raise RuntimeError(f"Refusing non-QA/unapproved host: {host or '<missing>'}")


for _url in (ISSUER, REDIRECT, API_BASE, MAIL_API):
    ensure_qa_url(_url)


def utc_stamp(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def load_secrets() -> dict:
    data = read_json(SECRET_FILE, {"version": 1, "accounts": {}, "mailboxes": {}})
    data.setdefault("accounts", {})
    data.setdefault("mailboxes", {})
    return data


def save_secrets(data: dict) -> None:
    write_json(SECRET_FILE, data)


def random_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if (re.search(r"[a-z]", value) and re.search(r"[A-Z]", value)
                and re.search(r"\d", value) and re.search(r"[^A-Za-z0-9]", value)):
            return value


def slug(alias: str) -> str:
    return alias.lower().replace("qa-", "").replace("-01", "").replace("-", "")


def mail_headers(token: str | None = None) -> dict:
    return {"Authorization": f"Bearer {token}"} if token else {}


def mail_domains() -> list[str]:
    response = requests.get(MAIL_API + "/domains?page=1", timeout=30)
    response.raise_for_status()
    rows = response.json().get("hydra:member", [])
    return [row["domain"] for row in rows if row.get("isActive")]


def create_mailbox(alias: str, secrets_data: dict) -> dict:
    existing = secrets_data["mailboxes"].get(alias)
    if existing:
        verify_mailbox(existing)
        return existing
    domains = mail_domains()
    if not domains:
        raise RuntimeError("Test mailbox service returned no active domains")
    password = random_password()
    # mail.tm currently rejects long local parts; keep a readable alias stem
    # while retaining enough random suffix for collision resistance.
    prefix = f"p392-{slug(alias)[:16]}-{secrets.token_hex(3)}"
    address = f"{prefix}@{domains[0]}"
    response = None
    for attempt in range(8):
        response = requests.post(MAIL_API + "/accounts", json={
            "address": address, "password": password,
        }, timeout=30)
        if response.status_code != 429:
            break
        if attempt == 7:
            break
        time.sleep(min(30, 6 + attempt * 3))
    assert response is not None
    if not response.ok:
        detail = response.text[:500].replace(password, "[REDACTED]")
        raise RuntimeError(f"Mailbox creation failed: HTTP {response.status_code}: {detail}")
    account_id = response.json()["id"]
    token_response = requests.post(MAIL_API + "/token", json={
        "address": address, "password": password,
    }, timeout=30)
    token_response.raise_for_status()
    record = {
        "address": address,
        "mail_password": password,
        "mail_token": token_response.json()["token"],
        "mail_account_id": account_id,
        "verified_access_at": utc_stamp(dt.datetime.now(dt.timezone.utc)),
    }
    secrets_data["mailboxes"][alias] = record
    save_secrets(secrets_data)
    verify_mailbox(record)
    return record


def verify_mailbox(mailbox: dict) -> None:
    response = requests.get(MAIL_API + "/messages?page=1",
                            headers=mail_headers(mailbox["mail_token"]), timeout=30)
    response.raise_for_status()


def list_messages(mailbox: dict) -> list[dict]:
    response = requests.get(MAIL_API + "/messages?page=1",
                            headers=mail_headers(mailbox["mail_token"]), timeout=30)
    response.raise_for_status()
    return response.json().get("hydra:member", [])


def message_body(mailbox: dict, message_id: str) -> str:
    response = requests.get(f"{MAIL_API}/messages/{message_id}",
                            headers=mail_headers(mailbox["mail_token"]), timeout=30)
    response.raise_for_status()
    payload = response.json()
    bodies = payload.get("html") or []
    if isinstance(bodies, str):
        bodies = [bodies]
    return html.unescape("\n".join(bodies + [payload.get("text") or ""]))


def action_link(text: str) -> str | None:
    for candidate in re.findall(r'https?://[^\s"<>]+', text):
        candidate = candidate.rstrip(".,);'")
        parsed = urlparse(candidate)
        if parsed.hostname == "keycloak.dev.platform.glucorx.co.uk" and (
                "action-token" in parsed.path or "execute-actions" in parsed.path):
            return candidate
    return None


def wait_for_action_link(mailbox: dict, known_ids: set[str], timeout: int = 180) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for message in list_messages(mailbox):
            if message["id"] in known_ids:
                continue
            link = action_link(message_body(mailbox, message["id"]))
            if link:
                ensure_qa_url(link)
                return link
        time.sleep(3)
    raise RuntimeError("Verification email did not arrive within the allowed wait")


def hidden_fields(form) -> dict:
    return {
        element.get("name"): element.get("value", "")
        for element in form.find_all("input")
        if element.get("name") and element.get("type") == "hidden"
    }


def context_string(source: str, key: str) -> str | None:
    match = re.search(rf'"{re.escape(key)}"\s*:\s*("(?:\\.|[^"\\])*")', source)
    return json.loads(match.group(1)) if match else None


def pkce_start(session: requests.Session, *, prompt: str | None = None):
    session.headers.setdefault("User-Agent", "Mozilla/5.0 QA-Fixture-Provisioner/1.0")
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": CLIENT,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": "openid",
        "state": state,
        "nonce": secrets.token_urlsafe(24),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "response_mode": "fragment",
    }
    if prompt:
        params["prompt"] = prompt
    url = ISSUER + "/protocol/openid-connect/auth?" + urlencode(params)
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response, verifier, state


def registration_form(session: requests.Session):
    # Start at the ordinary sign-in page and follow the realm-provided
    # registration link.  The realm advertises prompt=create in discovery but
    # its current theme does not expose the registration form through that
    # prompt consistently.
    page, _, _ = pkce_start(session)
    soup = BeautifulSoup(page.text, "html.parser")
    form = soup.find("form", id="kc-register-form")
    if form is None:
        link = soup.find("a", href=re.compile(r"registration"))
        href = link.get("href") if link is not None else None
        if href is None:
            # The Keycloakify theme renders the form client-side; the server
            # places the trusted registration URL in kcContext.
            match = re.search(
                r'"registrationUrl"\s*:\s*("(?:\\.|[^"\\])*")', page.text
            )
            href = json.loads(match.group(1)) if match else None
        if href is None:
            visible = soup.get_text(" ", strip=True)[:500]
            raise RuntimeError(
                f"QA registration form/link was not returned from {page.url}: {visible}"
            )
        page = session.get(urljoin(page.url, href), timeout=30)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        form = soup.find("form", id="kc-register-form") or soup.find("form")
    if form is not None:
        action = urljoin(page.url, form.get("action", ""))
    else:
        match = re.search(
            r'"registrationAction"\s*:\s*("(?:\\.|[^"\\])*")', page.text
        )
        if not match:
            raise RuntimeError("QA registration action was not returned")
        action = urljoin(page.url, json.loads(match.group(1)))
    ensure_qa_url(action)
    return form, action


def register_account(alias: str, region: str, given: str, family: str,
                     verify_email: bool, secrets_data: dict) -> dict:
    existing = secrets_data["accounts"].get(alias)
    if existing:
        return existing
    mailbox = create_mailbox(alias, secrets_data)
    before = {item["id"] for item in list_messages(mailbox)}
    password = secrets_data.setdefault("shared_app_password", random_password())
    save_secrets(secrets_data)
    session = requests.Session()
    form, action = registration_form(session)
    fields = hidden_fields(form) if form is not None else {}
    fields.update({
        "email": mailbox["address"],
        "password": password,
        "password-confirm": password,
        "firstName": given,
        "lastName": family,
        "region": region,
    })
    response = session.post(action, data=fields, timeout=30, allow_redirects=True)
    response.raise_for_status()
    visible = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
    errors = [node.get_text(" ", strip=True) for node in
              BeautifulSoup(response.text, "html.parser").select(".alert-error,.pf-m-danger,.kc-feedback-text")]
    if errors and not any("verify" in err.lower() or "email" in err.lower() for err in errors):
        raise RuntimeError("QA registration was rejected: " + " | ".join(errors))
    record = {
        "alias": alias,
        "email": mailbox["address"],
        "password": password,
        "region": region,
        "given_name": given,
        "family_name": family,
        "email_verified": False,
        "registration_result": "submitted",
    }
    secrets_data["accounts"][alias] = record
    save_secrets(secrets_data)
    if verify_email:
        link = wait_for_action_link(mailbox, before)
        confirm = session.get(link, timeout=30, allow_redirects=True)
        confirm.raise_for_status()
        page_id = context_string(confirm.text, "pageId")
        summary = context_string(confirm.text, "summary") or ""
        record["email_verified"] = (
            "verified" in summary.lower() or page_id not in {"login-verify-email", "error"}
        )
        record["verified_at"] = utc_stamp(dt.datetime.now(dt.timezone.utc))
        record["verification_result"] = (
            "action-link-confirmed" if record["email_verified"] else "action-link-not-confirmed"
        )
    else:
        record["verification_result"] = "intentionally-unverified"
    record.pop("registration_result", None)
    secrets_data["accounts"][alias] = record
    save_secrets(secrets_data)
    return record


def resend_and_verify(account: dict, mailbox: dict) -> None:
    """Request a fresh Keycloak verification email and consume its action link."""
    session = requests.Session()
    page, _, _ = pkce_start(session)
    action = context_string(page.text, "loginAction")
    if not action:
        form = BeautifulSoup(page.text, "html.parser").find("form")
        action = urljoin(page.url, form.get("action", "")) if form else None
    if not action:
        raise RuntimeError("QA login action was unavailable for verification resend")
    response = session.post(action, data={
        "username": account["email"], "password": account["password"]
    }, timeout=30, allow_redirects=False)
    for _ in range(10):
        if response.status_code not in (301, 302, 303, 307, 308):
            break
        location = urljoin(response.url, response.headers["Location"])
        ensure_qa_url(location)
        response = session.get(location, timeout=30, allow_redirects=False)
    if response.status_code != 200 or context_string(response.text, "pageId") != "login-verify-email":
        raise RuntimeError(
            "QA account did not enter the expected verify-email action "
            f"(HTTP {response.status_code}, pageId={context_string(response.text, 'pageId')})"
        )
    resend = context_string(response.text, "loginAction")
    if not resend:
        raise RuntimeError("QA verify-email page did not expose its resend action")
    ensure_qa_url(resend)
    # Entering the required action can itself send a link.  Snapshot after that
    # transition, then request one fresh link so we cannot consume a token that
    # was invalidated by a later resend.
    known = {item["id"] for item in list_messages(mailbox)}
    sent = session.get(resend, timeout=30, allow_redirects=True)
    sent.raise_for_status()
    link = wait_for_action_link(mailbox, known)
    confirmed = session.get(link, timeout=30, allow_redirects=True)
    confirmed.raise_for_status()
    account["email_verified"] = True
    account["verified_at"] = utc_stamp(dt.datetime.now(dt.timezone.utc))
    account["verification_result"] = "fresh-action-link-opened"


def reset_account_password(account: dict, mailbox: dict, new_password: str,
                           allow_unverified: bool = False) -> None:
    """Reset one QA account through the realm's mailbox-backed recovery flow."""
    session = requests.Session()
    page, _, _ = pkce_start(session)
    reset_url = (context_string(page.text, "loginResetCredentialsUrl")
                 or context_string(page.text, "resetCredentialsUrl"))
    if not reset_url:
        soup = BeautifulSoup(page.text, "html.parser")
        link = soup.select_one("a[href*='reset-credentials']")
        reset_url = urljoin(page.url, link.get("href", "")) if link else None
    if not reset_url:
        raise RuntimeError("QA sign-in page did not expose password recovery")
    reset_url = urljoin(page.url, reset_url)
    ensure_qa_url(reset_url)

    known = {item["id"] for item in list_messages(mailbox)}
    reset_page = session.get(reset_url, timeout=30)
    reset_page.raise_for_status()
    soup = BeautifulSoup(reset_page.text, "html.parser")
    form = soup.find("form", id="kc-reset-password-form") or soup.find("form")
    if form is not None:
        action = urljoin(reset_page.url, form.get("action", ""))
        fields = hidden_fields(form)
    else:
        action = context_string(reset_page.text, "loginAction")
        fields = {}
    if not action:
        raise RuntimeError("QA password recovery form action was unavailable")
    action = urljoin(reset_page.url, action)
    ensure_qa_url(action)
    fields["username"] = account["email"]
    submitted = session.post(action, data=fields, timeout=30, allow_redirects=True)
    submitted.raise_for_status()

    link = wait_for_action_link(mailbox, known)
    update_page = session.get(link, timeout=30, allow_redirects=True)
    update_page.raise_for_status()
    soup = BeautifulSoup(update_page.text, "html.parser")
    form = soup.find("form", id="kc-passwd-update-form") or soup.find("form")
    if form is not None:
        action = urljoin(update_page.url, form.get("action", ""))
        fields = hidden_fields(form)
    else:
        action = context_string(update_page.text, "loginAction")
        fields = {}
    if not action:
        raise RuntimeError("QA password update form action was unavailable")
    action = urljoin(update_page.url, action)
    ensure_qa_url(action)
    fields.update({"password-new": new_password, "password-confirm": new_password})
    updated = session.post(action, data=fields, timeout=30, allow_redirects=True)
    updated.raise_for_status()
    visible = BeautifulSoup(updated.text, "html.parser").get_text(" ", strip=True)
    updated_page_id = context_string(updated.text, "pageId")
    updated_summary = context_string(updated.text, "summary") or ""
    errors = [node.get_text(" ", strip=True) for node in
              BeautifulSoup(updated.text, "html.parser").select(
                  ".alert-error,.pf-m-danger,.kc-feedback-text")]
    if errors and not any("updated" in item.lower() or "success" in item.lower()
                          for item in errors):
        raise RuntimeError("QA password update was rejected: " + " | ".join(errors))
    if updated_page_id in {"login-update-password", "error"}:
        raise RuntimeError(
            f"QA password update remained on pageId={updated_page_id}: "
            f"{updated_summary or visible[:300]}"
        )
    # OAuth authentication is the authoritative completion check.
    try:
        oauth_login(account["email"], new_password)
    except RuntimeError as error:
        if not (allow_unverified and "pageId=login-verify-email" in str(error)):
            raise


def account_accepts_password(account: dict, password: str,
                             allow_unverified: bool = False) -> bool:
    try:
        oauth_login(account["email"], password)
        return True
    except RuntimeError as error:
        return allow_unverified and "pageId=login-verify-email" in str(error)


def set_shared_password(only_alias: str | None = None) -> None:
    """Set one application password on every active PRT-0392 QA account."""
    new_password = getpass.getpass("New shared QA application password: ")
    confirmation = getpass.getpass("Confirm new password: ")
    if new_password != confirmation:
        raise RuntimeError("Password confirmation did not match")
    if len(new_password) < 8:
        raise RuntimeError("Password does not meet the minimum length")

    data = load_secrets()
    failures = []
    specs = [row for row in ACCOUNT_SPECS if not only_alias or row[0] == only_alias]
    if only_alias and not specs:
        raise RuntimeError(f"Unknown QA account alias: {only_alias}")
    for alias, _, _, _, is_verified in specs:
        account = data["accounts"].get(alias)
        mailbox = data["mailboxes"].get(alias)
        if not account or not mailbox:
            failures.append(f"{alias}: account or mailbox record missing")
            continue
        try:
            if not account_accepts_password(
                    account, new_password, allow_unverified=not is_verified):
                reset_account_password(
                    account, mailbox, new_password, allow_unverified=not is_verified)
            account["password"] = new_password
            account["password_updated_at"] = utc_stamp(dt.datetime.now(dt.timezone.utc))
            data["accounts"][alias] = account
            save_secrets(data)
            print(f"{alias}: password updated and sign-in verified")
        except Exception as error:  # continue so a partial run can be resumed safely
            failures.append(f"{alias}: {error}")
            print(f"{alias}: password update failed", file=sys.stderr)
    if failures:
        raise RuntimeError("Password update incomplete:\n" + "\n".join(failures))
    data["shared_app_password"] = new_password
    save_secrets(data)
    print(f"Updated and verified {len(specs)} QA account passwords")


def oauth_login(email: str, password: str) -> str:
    session = requests.Session()
    page, verifier, expected_state = pkce_start(session)
    soup = BeautifulSoup(page.text, "html.parser")
    form = soup.find("form", id="kc-form-login") or soup.find("form")
    if form is not None:
        action = urljoin(page.url, form.get("action", ""))
        fields = hidden_fields(form)
    else:
        match = re.search(r'"loginAction"\s*:\s*("(?:\\.|[^"\\])*")', page.text)
        if not match:
            raise RuntimeError("QA sign-in action was not returned")
        action = urljoin(page.url, json.loads(match.group(1)))
        fields = {}
    ensure_qa_url(action)
    fields.update(username=email, password=password)
    response = session.post(action, data=fields,
                            timeout=30, allow_redirects=False)
    for _ in range(12):
        if response.status_code not in (301, 302, 303, 307, 308):
            visible = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)[:600]
            signals = []
            for key in ("pageId", "summary", "messageHeader", "requiredActionUrl"):
                match = re.search(
                    rf'"{key}"\s*:\s*("(?:\\.|[^"\\])*")', response.text
                )
                if match:
                    signals.append(f"{key}={json.loads(match.group(1))}")
            url_keys = sorted(set(re.findall(r'"([A-Za-z][A-Za-z0-9]*(?:Url|Action))"\s*:', response.text)))
            if url_keys:
                signals.append("url_keys=" + ",".join(url_keys))
            raise RuntimeError(
                f"QA login failed or requires an unexpected action (HTTP {response.status_code}): "
                + ("; ".join(signals) or visible or "no visible message")
            )
        location = urljoin(response.url, response.headers["Location"])
        if location.startswith(REDIRECT):
            parsed_callback = urlparse(location)
            query = parse_qs(parsed_callback.query or parsed_callback.fragment)
            if query.get("state") != [expected_state] or not query.get("code"):
                raise RuntimeError("OAuth callback was invalid")
            token = session.post(ISSUER + "/protocol/openid-connect/token", data={
                "grant_type": "authorization_code",
                "client_id": CLIENT,
                "redirect_uri": REDIRECT,
                "code": query["code"][0],
                "code_verifier": verifier,
            }, timeout=30)
            token.raise_for_status()
            return token.json()["access_token"]
        ensure_qa_url(location)
        response = session.get(location, timeout=30, allow_redirects=False)
    raise RuntimeError("Too many redirects during QA login")


def rpc(method: str, body: dict, token: str) -> dict:
    url = API_BASE + SERVICE + method
    ensure_qa_url(url)
    response = requests.post(url, json=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Connect-Protocol-Version": "1",
    }, timeout=60)
    if not response.ok:
        raise RuntimeError(f"{method}: HTTP {response.status_code}: {response.text[:800]}")
    return response.json() if response.content else {}


def paged(method: str, body: dict, key: str, token: str) -> list[dict]:
    rows, page_token = [], ""
    while True:
        request = dict(body)
        if page_token:
            request["page_token"] = page_token
        result = rpc(method, request, token)
        rows.extend(result.get(key, []))
        page_token = result.get("nextPageToken") or result.get("next_page_token") or ""
        if not page_token:
            return rows


def patient_profile(alias: str) -> dict:
    profiles = {
        "QA-MAIN-01": ("QA Main Patient", "America/New_York", "US"),
        "QA-HISTORY-01": ("QA History Patient", "Asia/Karachi", "PK"),
        "QA-NODATA-01": ("QA No Data Patient", "Europe/London", "GB"),
        "QA-LOGIN-US-01": ("QA Login US Patient", "America/New_York", "US"),
    }
    display, zone, country = profiles.get(alias, (alias.replace("-", " "), "Europe/London", "GB"))
    return {
        "display_name": display,
        "time_zone": zone,
        "country": country,
        "date_of_birth": {"year": 1990, "month": 3, "day": 15},
        "diabetes_type": "TYPE_1",
        "phone": "+442025550123",
    }


def ensure_patient(alias: str, account: dict) -> tuple[str, str]:
    try:
        token = oauth_login(account["email"], account["password"])
    except RuntimeError as error:
        if "pageId=login-verify-email" not in str(error):
            raise
        data = load_secrets()
        mailbox = data["mailboxes"].get(alias)
        if not mailbox:
            raise RuntimeError(f"{alias} has no saved mailbox for email verification") from None
        resend_and_verify(account, mailbox)
        data["accounts"][alias] = account
        save_secrets(data)
        token = oauth_login(account["email"], account["password"])
    user = rpc("GetUser", {"name": "users/me"}, token)
    patient = user.get("selfPatient")
    desired = patient_profile(alias)
    if not patient:
        created = rpc("CreatePatient", {
            "patient_id": str(uuid.uuid5(uuid.NAMESPACE_URL, user["name"] + ":" + alias)),
            "patient": desired,
        }, token)
        patient = created["name"]
    rpc("UpdatePatient", {
        "patient": {"name": patient, **desired},
        "update_mask": "displayName,timeZone,country,dateOfBirth,diabetesType,phone",
    }, token)
    rpc("UpdatePatientSettings", {"patient_settings": {
        "name": patient + "/settings",
        "urgent_low_centi_mg_dl": 5400,
        "low_centi_mg_dl": 7000,
        "high_centi_mg_dl": 18000,
        "urgent_high_centi_mg_dl": 25000,
    }}, token)
    account["user"] = user["name"]
    account["self_patient"] = patient
    account["onboarding_backend_profile"] = "complete"
    return token, patient


def create_session(patient: str, transmitter: str, start: dt.datetime,
                   token: str, label: str) -> str:
    session_id = str(uuid.uuid5(uuid.NAMESPACE_URL, patient + ":" + label))
    expected = patient + "/sessions/" + session_id
    sessions = paged("ListSessions", {"parent": patient}, "sessions", token)
    transmitter_name = "transmitters/" + transmitter
    found = next((row for row in sessions if row.get("name") == expected
                  or row.get("transmitter") == transmitter_name), None)
    if found:
        return found["name"]
    created = rpc("CreateSession", {
        "parent": patient,
        "session_id": session_id,
        "session": {
            "transmitter": transmitter_name,
            "session_index": "1",
            "start_time": utc_stamp(start),
            "firmware_version": {
                "major": 3, "minor": 1, "patch": 0,
                "image_sha256": hashlib.sha256(("PRT0392 " + label).encode()).hexdigest(),
            },
            "app_build": {"platform": "IOS", "version": "1.0.4"},
        },
    }, token)
    return created["name"]


def write_readings(session: str, rows: list[dict], token: str) -> int:
    existing = paged("QueryReadings", {"parent": session}, "readings", token)
    have = {int(row["index"]) for row in existing}
    pending = [row for row in rows if row["index"] not in have]
    for offset in range(0, len(pending), 200):
        result = rpc("WriteReadings", {
            "parent": session,
            "partial_success": False,
            "readings": pending[offset:offset + 200],
        }, token)
        if result.get("failedReadings") or result.get("failed_readings"):
            raise RuntimeError("Backend rejected one or more glucose readings")
    return len(pending)


def history_rows(now: dt.datetime) -> list[dict]:
    pkt = dt.timezone(dt.timedelta(hours=5))
    local_now = now.astimezone(pkt).replace(second=0, microsecond=0)
    minute_delta = (local_now.minute - 2) % 5
    end = (local_now - dt.timedelta(minutes=minute_delta)).astimezone(dt.timezone.utc)
    start = end - dt.timedelta(days=90)
    pinned = dt.datetime(2026, 10, 1, 7, 22, tzinfo=pkt).astimezone(dt.timezone.utc)
    gap_start = end - dt.timedelta(days=2, hours=3)
    gap_end = gap_start + dt.timedelta(hours=1)
    rows, when, index = [], start, 1
    while when <= end:
        if not gap_start <= when < gap_end:
            local = when.astimezone(pkt)
            phase = (local.hour * 60 + local.minute) / 1440 * 2 * math.pi
            value = 118 + 32 * math.sin(phase) + 18 * math.sin(index / 37)
            band = index % 97
            if band == 0:
                value = 52
            elif band in (1, 2):
                value = 63
            elif band in (3, 4, 5, 6):
                value = 205
            if when == pinned:
                value = 125.45
            rows.append({
                "index": index,
                "measure_time": utc_stamp(when),
                "glucose_centi_mg_dl": round(value * 100),
            })
        when += dt.timedelta(minutes=5)
        index += 1
    return rows


def split_rows(rows: list[dict], max_days: int = 14) -> list[list[dict]]:
    groups: list[list[dict]] = []
    for row in rows:
        when = dt.datetime.fromisoformat(row["measure_time"].replace("Z", "+00:00"))
        if not groups:
            groups.append([])
        first = (dt.datetime.fromisoformat(groups[-1][0]["measure_time"].replace("Z", "+00:00"))
                 if groups[-1] else when)
        if when - first >= dt.timedelta(days=max_days):
            groups.append([])
        groups[-1].append(row)
    return groups


def seed_history(account: dict) -> dict:
    token, patient = ensure_patient("QA-HISTORY-01", account)
    all_rows = history_rows(dt.datetime.now(dt.timezone.utc))
    sessions = []
    written = 0
    for number, group in enumerate(split_rows(all_rows), 1):
        # Reading indexes are scoped to a session.
        rows = [dict(row, index=i) for i, row in enumerate(group, 1)]
        name = create_session(patient, f"QAHIST{number:02d}",
                              dt.datetime.fromisoformat(rows[0]["measure_time"].replace("Z", "+00:00")),
                              token, f"history-{number}")
        written += write_readings(name, rows, token)
        sessions.append(name)
        current = rpc("GetSession", {"name": name}, token)
        if number < len(split_rows(all_rows)) and current.get("state") == "ACTIVE":
            rpc("StopSession", {"name": name}, token)
    seed_history_events(patient, sessions[-1], token)
    return {"patient": patient, "sessions": sessions, "reading_count": len(all_rows),
            "new_readings": written, "refreshed_at": utc_stamp(dt.datetime.now(dt.timezone.utc))}


def seed_history_events(patient: str, latest_session: str, token: str) -> None:
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    event_specs = []
    meals = [("Breakfast", 45), ("Lunch", 70), ("Dinner", 85), ("Snack", 20)]
    for i, (name, grams) in enumerate(meals):
        event_specs.append((f"meal-{i}", now - dt.timedelta(days=i * 3 + 1, hours=4),
                            {"carbohydrate": {"grams": grams, "calories": grams * 4,
                                              "fat_grams": 0}}))
    insulin = ["Rapid-acting", "Short-acting", "Intermediate-acting", "Mixed", "Long-acting"]
    for i, product in enumerate(insulin):
        event_specs.append((f"insulin-{i}", now - dt.timedelta(days=i * 4 + 2, hours=3),
                            {"insulin": {"units": 0.5 + i * 5.5,
                                         "kind": "BOLUS" if i < 2 else "BASAL",
                                         "product": product}}))
    activities = ["Walking", "Running", "Jogging", "Cycling", "Swimming", "Other"]
    intensities = ["LOW", "MODERATE", "HIGH"]
    for i, activity in enumerate(activities):
        event_specs.append((f"activity-{i}", now - dt.timedelta(days=i * 4 + 1, hours=2),
                            {"activity": {"activity_type": activity,
                                          "duration_minutes": [1, 30, 60, 120, 480, 960][i],
                                          "intensity": intensities[i % 3]}}))
    for i, text in enumerate(("Flu", "Synthetic QA sickness note", "Headache - QA fixture only")):
        event_specs.append((f"note-{i}", now - dt.timedelta(days=i * 5 + 1, hours=1),
                            {"note": {"text": text, "category": "SICKNESS"}}))
    event_specs.append(("note-boundary-30d", now - dt.timedelta(days=29, hours=1),
                        {"note": {"text": "QA sickness note at 30-day boundary",
                                  "category": "SICKNESS"}}))
    existing = paged("ListEvents", {"parent": patient}, "events", token)
    existing_names = {row.get("name") for row in existing}
    for key, when, detail in event_specs:
        event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, patient + ":" + key))
        expected = patient + "/events/" + event_id
        if expected in existing_names:
            continue
        rpc("CreateEvent", {"parent": patient, "event_id": event_id,
                            "request_id": event_id,
                            "event": {"event_time": utc_stamp(when), **detail}}, token)
    calibrations = paged("ListCalibrations", {"parent": latest_session}, "calibrations", token)
    existing_cal = {row.get("name") for row in calibrations}
    for i in range(14):
        cal_id = str(uuid.uuid5(uuid.NAMESPACE_URL, latest_session + f":cal-{i}"))
        expected = latest_session + "/calibrations/" + cal_id
        if expected in existing_cal:
            continue
        rpc("CreateCalibration", {"parent": latest_session, "calibration_id": cal_id,
                                   "calibration": {
                                       "reference_glucose_centi_mg_dl": 10000 + i * 100,
                                       "measure_time": utc_stamp(now - dt.timedelta(days=i, hours=5)),
                                   }}, token)


def seed_nodata(account: dict) -> dict:
    token, patient = ensure_patient("QA-NODATA-01", account)
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    start, end = now - dt.timedelta(hours=72), now - dt.timedelta(hours=25)
    values = [5200, 6500, 9000, 14000, 19000, 22000]
    rows, when, index = [], start, 1
    while when <= end:
        rows.append({"index": index, "measure_time": utc_stamp(when),
                     "glucose_centi_mg_dl": values[(index - 1) % len(values)]})
        when += dt.timedelta(minutes=5)
        index += 1
    session = create_session(patient, "QANODATA01", start, token, "no-data")
    written = write_readings(session, rows, token)
    current = rpc("GetSession", {"name": session}, token)
    if current.get("state") == "ACTIVE":
        rpc("StopSession", {"name": session}, token)
    return {"patient": patient, "session": session, "reading_count": len(rows),
            "new_readings": written, "latest_reading": rows[-1]["measure_time"],
            "refreshed_at": utc_stamp(dt.datetime.now(dt.timezone.utc))}


def provision_accounts() -> None:
    data = load_secrets()
    for alias in MAILBOX_ONLY:
        create_mailbox(alias, data)
        print(f"MAILBOX READY {alias}", flush=True)
    for alias, region, given, family, verified in ACCOUNT_SPECS:
        account = register_account(alias, region, given, family, verified, data)
        if verified and alias not in NO_BACKEND_ONBOARDING:
            ensure_patient(alias, account)
            data["accounts"][alias] = account
            save_secrets(data)
        print(f"ACCOUNT READY {alias}", flush=True)
    write_public_report(data)


def rotate_fresh_account() -> None:
    """Replace QA-FRESH-01 without deleting the earlier QA account."""
    data = load_secrets()
    alias = "QA-FRESH-01"
    suffix = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if alias in data["accounts"]:
        data["accounts"][f"{alias}-RETIRED-{suffix}"] = data["accounts"].pop(alias)
    if alias in data["mailboxes"]:
        data["mailboxes"][f"{alias}-RETIRED-{suffix}"] = data["mailboxes"].pop(alias)
    save_secrets(data)
    account = register_account(alias, "uk", "QA Fresh", "Account", True, data)
    if account.get("self_patient"):
        raise RuntimeError("Replacement QA-FRESH-01 unexpectedly has a backend patient")
    write_public_report(data)
    print("QA-FRESH-01 replaced with a verified account that has no backend patient")


def refresh() -> None:
    data = load_secrets()
    required = {"QA-HISTORY-01", "QA-NODATA-01"}
    if not required.issubset(data["accounts"]):
        raise RuntimeError("Run provision first; history/no-data accounts are missing")
    state = read_json(STATE_FILE, {"version": 1})
    state["history"] = seed_history(data["accounts"]["QA-HISTORY-01"])
    write_json(STATE_FILE, state)
    state["no_data"] = seed_nodata(data["accounts"]["QA-NODATA-01"])
    state["generated_at"] = utc_stamp(dt.datetime.now(dt.timezone.utc))
    write_json(STATE_FILE, state)
    save_secrets(data)
    write_public_report(data, state)
    print("PRT-0392 rolling seed refresh completed")


def write_public_report(data: dict, state: dict | None = None) -> None:
    rows = []
    for alias, region, _, _, verified in ACCOUNT_SPECS:
        account = data["accounts"].get(alias, {})
        profile = patient_profile(alias)
        registration_region = "United States" if region == "us" else "United Kingdom"
        display_region = "Pakistan (PK)" if alias == "QA-HISTORY-01" else registration_region
        rows.append({
            "reference_id": alias,
            "email": account.get("email", "[ Enter email ]"),
            "region": display_region,
            "registration_region": registration_region,
            "patient_country": profile["country"],
            "unit": "mg/dL" if region == "us" else "mmol/L",
            "state": ("registered; email intentionally unverified" if not verified
                      else "verified; onboarding never started" if alias == "QA-FRESH-01"
                      else "verified; backend profile complete" if account.get("self_patient")
                      else "verified; backend profile not required"),
            "mailbox_access": "verified" if alias in data["mailboxes"] else "missing",
        })
    report = {
        "generated_at": utc_stamp(dt.datetime.now(dt.timezone.utc)),
        "environment": {"issuer": ISSUER, "api": API_BASE},
        "accounts": rows,
        "mailbox_only": [
            {"reference_id": alias,
             "email": data["mailboxes"].get(alias, {}).get("address", "[ Enter email ]"),
             "mailbox_access": "verified" if alias in data["mailboxes"] else "missing"}
            for alias in MAILBOX_ONLY
        ],
        "seed": state or read_json(STATE_FILE, {}),
    }
    write_json(REPORT_FILE, report)


def verify_seed_data(data: dict) -> list[str]:
    state = read_json(STATE_FILE, {})
    failures: list[str] = []
    now = dt.datetime.now(dt.timezone.utc)

    history_account = data["accounts"].get("QA-HISTORY-01")
    history_state = state.get("history", {})
    if not history_account or not history_state.get("sessions"):
        failures.append("QA-HISTORY-01: rolling fixture state missing")
    else:
        token = oauth_login(history_account["email"], history_account["password"])
        readings = []
        for session in history_state["sessions"]:
            readings.extend(paged("QueryReadings", {"parent": session}, "readings", token))
        timeline = sorted((
            dt.datetime.fromisoformat(row["measureTime"].replace("Z", "+00:00")),
            int(row["glucoseCentiMgDl"]),
        ) for row in readings)
        pinned_time = dt.datetime(2026, 10, 1, 2, 22, tzinfo=dt.timezone.utc)
        pinned = [value for when, value in timeline if when == pinned_time]
        recent_gaps = [
            (a, b) for (a, _), (b, _) in zip(timeline, timeline[1:])
            if b - a >= dt.timedelta(minutes=65) and b >= now - dt.timedelta(days=7)
        ]
        values = [value for _, value in timeline]
        events = paged("ListEvents", {"parent": history_state["patient"]}, "events", token)
        note_texts = {
            event.get("note", {}).get("text")
            for event in events if event.get("note")
        }
        required_sickness_notes = {
            "Flu",
            "Synthetic QA sickness note",
            "Headache - QA fixture only",
            "QA sickness note at 30-day boundary",
        }
        calibrations = paged("ListCalibrations", {
            "parent": history_state["sessions"][-1]
        }, "calibrations", token)
        checks = {
            "reading_count_matches": len(timeline) == history_state.get("reading_count"),
            "full_90_day_span": bool(timeline) and (
                timeline[-1][0] - timeline[0][0] >= dt.timedelta(days=90)),
            "pinned_2026_10_01_0722_pkt": pinned == [12545],
            "recent_full_hour_gap": bool(recent_gaps),
            "severe_low_present": any(value <= 5600 for value in values),
            "low_present": any(5700 <= value <= 6900 for value in values),
            "in_range_present": any(7000 <= value <= 18000 for value in values),
            "high_present": any(value > 18000 for value in values),
            "events_present": len(events) >= 19,
            "sickness_notes_present": required_sickness_notes <= note_texts,
            "exactly_14_calibrations": len(calibrations) == 14,
        }
        history_state["verification"] = {
            **checks,
            "remote_reading_count": len(timeline),
            "remote_event_count": len(events),
            "remote_calibration_count": len(calibrations),
            "verified_at": utc_stamp(now),
        }
        failures.extend(f"QA-HISTORY-01: {name}" for name, passed in checks.items() if not passed)

    nodata_account = data["accounts"].get("QA-NODATA-01")
    nodata_state = state.get("no_data", {})
    if not nodata_account or not nodata_state.get("session"):
        failures.append("QA-NODATA-01: rolling fixture state missing")
    else:
        token = oauth_login(nodata_account["email"], nodata_account["password"])
        readings = paged("QueryReadings", {"parent": nodata_state["session"]}, "readings", token)
        latest = max(dt.datetime.fromisoformat(row["measureTime"].replace("Z", "+00:00"))
                     for row in readings)
        checks = {
            "latest_24_hours_empty": latest < now - dt.timedelta(hours=24),
            "three_days_populated": latest >= now - dt.timedelta(days=3),
            "reading_count_matches": len(readings) == nodata_state.get("reading_count"),
        }
        nodata_state["verification"] = {
            **checks,
            "remote_reading_count": len(readings),
            "remote_latest_reading": utc_stamp(latest),
            "verified_at": utc_stamp(now),
        }
        failures.extend(f"QA-NODATA-01: {name}" for name, passed in checks.items() if not passed)

    state["history"] = history_state
    state["no_data"] = nodata_state
    write_json(STATE_FILE, state)
    return failures


def verify() -> None:
    data = load_secrets()
    failures = []
    for alias in [row[0] for row in ACCOUNT_SPECS] + MAILBOX_ONLY:
        mailbox = data["mailboxes"].get(alias)
        if not mailbox:
            failures.append(f"{alias}: mailbox missing")
            continue
        try:
            verify_mailbox(mailbox)
        except Exception as error:
            failures.append(f"{alias}: mailbox inaccessible ({type(error).__name__})")
    for alias, _, _, _, verified in ACCOUNT_SPECS:
        account = data["accounts"].get(alias)
        if not account:
            failures.append(f"{alias}: account missing")
            continue
        if verified:
            try:
                token = oauth_login(account["email"], account["password"])
                user = rpc("GetUser", {"name": "users/me"}, token)
                if user.get("selfPatient") != account.get("self_patient"):
                    failures.append(f"{alias}: patient binding mismatch")
            except Exception as error:
                failures.append(f"{alias}: login/API verification failed ({type(error).__name__})")
    failures.extend(verify_seed_data(data))
    write_public_report(data)
    if failures:
        print("\n".join(failures))
        raise RuntimeError(f"Verification failed for {len(failures)} item(s)")
    print("All saved mailboxes are accessible and all verified accounts pass QA login/API checks")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("provision", help="Create mailboxes/accounts and backend profiles")
    sub.add_parser("rotate-fresh", help="Replace QA-FRESH-01 without backend onboarding")
    sub.add_parser("refresh", help="Refresh rolling history and no-data fixtures")
    sub.add_parser("verify", help="Verify mailbox access, sign-in, and API binding")
    password_parser = sub.add_parser(
        "set-password", help="Reset every active QA account password")
    password_parser.add_argument("--alias", help="Limit the reset to one QA alias")
    args = parser.parse_args()
    try:
        if args.command == "provision":
            provision_accounts()
        elif args.command == "rotate-fresh":
            rotate_fresh_account()
        elif args.command == "refresh":
            refresh()
        elif args.command == "set-password":
            set_shared_password(args.alias)
        else:
            verify()
    except requests.RequestException as error:
        raise RuntimeError(f"QA network request failed: {type(error).__name__}") from None


if __name__ == "__main__":
    main()
