#!/usr/bin/env python3
"""Initialize Farmce credentials.

Sends a magic link to the user's Farmce email, then prompts them to
paste the Bearer token from the callback page. Saves everything to
assets/config.json (excluded from git).

Usage:
    python scripts/init_config.py
    python scripts/init_config.py --base-url https://app.farmce.com
"""

import sys
import os
import argparse

import requests

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scripts.utils import save_config

DEFAULT_BASE_URL = "https://app.farmce.com"


def send_magic_link(base_url: str, email: str) -> dict:
    resp = requests.post(
        f"{base_url}/api/auth/token/magic-link",
        headers={"Content-Type": "application/json"},
        json={"email": email},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Initialize Farmce credentials")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help=f"Farmce backend URL (default: {DEFAULT_BASE_URL})")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    print("=" * 60)
    print("  Farmce Skill — Credential Setup")
    print("=" * 60)
    print(f"\nBackend: {base_url}")

    email = input("\nEnter your Farmce account email: ").strip()
    if not email:
        print("❌ Email is required.")
        sys.exit(1)

    print(f"\nSending magic link to {email}...")
    try:
        result = send_magic_link(base_url, email)
    except requests.HTTPError as e:
        print(f"❌ Failed to send magic link: {e.response.status_code} {e.response.text}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        sys.exit(1)

    print(f"✅ Magic link sent! ({result.get('message', 'ok')})")
    print("\nSteps:")
    print("  1. Open your email and click the magic link.")
    print("  2. You will be redirected to a callback page.")
    print("  3. Copy the Bearer token from that page.")
    print("  4. Paste it below.\n")

    token = input("Paste Bearer token here: ").strip()
    if not token:
        print("❌ Token is required.")
        sys.exit(1)

    # Strip "Bearer " prefix if user copied it
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    cfg = {
        "base_url": base_url,
        "bearer_token": token,
    }
    save_config(cfg)

    print("\n✅ Saved to assets/config.json")
    print("\nRun doctor to verify:")
    print("  python scripts/doctor.py")


if __name__ == "__main__":
    main()
