#!/usr/bin/env python3
"""
firebase_auth.py – Firebase Authentication helper for push scripts.

Usage:
  from firebase_auth import get_auth_token, firebase_put, firebase_patch

Setup (one-time):
  1. In Firebase Console → Authentication → Users → Add user
     Email: scripts@thara-crm.internal
     Password: choose a strong password
  2. Create a file called .firebase_credentials (in the same folder, NOT committed to git)
     with two lines:
       email=scripts@thara-crm.internal
       password=YOUR_STRONG_PASSWORD
  3. Make sure .firebase_credentials is in .gitignore  ✓ (already added)
"""

import json
import os
import ssl
import urllib.request
import urllib.error
from pathlib import Path

# ── Firebase project config ──
FIREBASE_API_KEY = "AIzaSyCxaaz39phlKXsjDW9YIKBnqBeVI1l0Sy0"
FIREBASE_URL     = "https://hanzaha-d558c-default-rtdb.europe-west1.firebasedatabase.app"

ssl_ctx = ssl.create_default_context()   # validates Firebase TLS certificate

_CRED_FILE = Path(__file__).parent / ".firebase_credentials"


def _load_credentials():
    """Load service-account credentials from .firebase_credentials file."""
    if not _CRED_FILE.exists():
        raise FileNotFoundError(
            f"Missing credentials file: {_CRED_FILE}\n"
            "Create it with:\n  email=scripts@thara-crm.internal\n  password=YOUR_PASSWORD"
        )
    creds = {}
    for line in _CRED_FILE.read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            creds[k.strip()] = v.strip()
    return creds["email"], creds["password"]


def get_auth_token() -> str:
    """Sign in with Firebase Auth and return a fresh ID token."""
    email, password = _load_credentials()
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
        f"?key={FIREBASE_API_KEY}"
    )
    payload = json.dumps({
        "email": email,
        "password": password,
        "returnSecureToken": True
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, context=ssl_ctx) as resp:
        data = json.loads(resp.read())
    return data["idToken"]


def _request(method: str, path: str, data=None, token: str = None) -> dict:
    """Generic authenticated Firebase REST request."""
    if token is None:
        token = get_auth_token()
    url = f"{FIREBASE_URL}/{path}.json?auth={token}"
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(
        url, data=payload, method=method,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, context=ssl_ctx) as resp:
        return json.loads(resp.read())


def firebase_put(path: str, data: dict, token: str = None) -> dict:
    """Write (overwrite) a node at path."""
    return _request("PUT", path, data, token)


def firebase_patch(path: str, data: dict, token: str = None) -> dict:
    """Update (merge) a node at path."""
    return _request("PATCH", path, data, token)


def firebase_post(path: str, data: dict, token: str = None) -> dict:
    """Push a new child at path."""
    return _request("POST", path, data, token)


def firebase_get(path: str, token: str = None) -> dict:
    """Read a node at path."""
    return _request("GET", path, token=token)
