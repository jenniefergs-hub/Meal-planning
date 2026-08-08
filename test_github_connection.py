"""
Connection test for GitHub.

Run directly:
    python test_github_connection.py

Run with pytest:
    pytest test_github_connection.py

Set GITHUB_TOKEN in the environment to also verify authenticated access
(GET /user). Without it, only the public, unauthenticated API check runs.
"""

import json
import os
import urllib.error
import urllib.request

GITHUB_API_URL = "https://api.github.com"


def check_public_api() -> dict:
    """Hit the unauthenticated GitHub API root to confirm basic connectivity."""
    request = urllib.request.Request(
        GITHUB_API_URL,
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise ConnectionError(f"Unexpected status code: {response.status}")
        return json.loads(response.read())


def check_authenticated_api(token: str) -> dict:
    """Hit GET /user using a token to confirm the credential is valid."""
    request = urllib.request.Request(
        f"{GITHUB_API_URL}/user",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200:
            raise ConnectionError(f"Unexpected status code: {response.status}")
        return json.loads(response.read())


def test_public_api_reachable():
    data = check_public_api()
    assert "current_user_url" in data


def test_authenticated_api_if_token_present():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return  # nothing to verify without credentials
    data = check_authenticated_api(token)
    assert "login" in data


def main() -> int:
    print("Testing connection to GitHub API...")
    try:
        check_public_api()
        print("[OK] Public API reachable:", GITHUB_API_URL)
    except (urllib.error.URLError, ConnectionError) as exc:
        print("[FAIL] Could not reach GitHub API:", exc)
        return 1

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[SKIP] GITHUB_TOKEN not set; skipping authenticated check.")
        return 0

    try:
        user = check_authenticated_api(token)
        print(f"[OK] Authenticated as: {user.get('login')}")
    except (urllib.error.URLError, ConnectionError) as exc:
        print("[FAIL] Authenticated request failed:", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
