#!/usr/bin/env python3
"""Delete a Farmce profile with mandatory interactive confirmation.

AI agents MUST follow the deletion workflow in SKILL.md:
  1. List profiles and show IDs to the user
  2. Ask for explicit confirmation (profile ID + YES)
  3. STOP AND WAIT for the user reply
  4. Only then run this script in an interactive terminal

Usage:
    python scripts/delete_helper.py
    python scripts/delete_helper.py --profile-id <id>   # still requires interactive YES

Anti-automation:
  - Requires a real TTY (stdin/stdout)
  - Requires re-typing the profile ID and YES
  - Enforced delay before the API call
  - client.delete_profile(..., confirmed=False) is blocked
"""

import sys
import os
import time
import json
import argparse
from typing import Optional

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scripts.farmce_client import FarmceClient
from scripts.error_codes import ErrorCode, StructuredError, classify_error

CONFIRM_DELAY_S = 3
BUSY_STATUSES = ("running", "starting", "creating", "stopping")


def require_tty() -> Optional[StructuredError]:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        err = StructuredError(ErrorCode.DELETE_REQUIRES_TTY)
        err.print()
        return err
    return None


def list_profiles_table(client: FarmceClient) -> list:
    resp = client.list_profiles()
    profiles = resp.get("profiles") or resp.get("data") or []
    if isinstance(profiles, dict):
        profiles = profiles.get("profiles") or []

    print("\nCurrent profiles:")
    print(f"{'ID':<40} {'Name':<24} {'Status':<12}")
    print("-" * 80)
    if not profiles:
        print("(none)")
        return []
    for p in profiles:
        pid = p.get("id", "?")
        name = (p.get("name") or "")[:24]
        status = p.get("status") or "?"
        print(f"{pid:<40} {name:<24} {status:<12}")
    print()
    return profiles


def confirm_and_delete(profile_id: str, client: FarmceClient = None) -> dict:
    """Interactive confirm then delete.

    Returns:
        {"ok": True, "profileId": ...} on success
        {"ok": False, "error": StructuredError.to_dict()} on failure
    """
    tty_err = require_tty()
    if tty_err:
        return {"ok": False, "error": tty_err.to_dict()}

    if not profile_id or not str(profile_id).strip():
        err = StructuredError(ErrorCode.DELETE_NOT_CONFIRMED, message="profile_id is empty")
        err.print()
        return {"ok": False, "error": err.to_dict()}

    profile_id = str(profile_id).strip()
    c = client or FarmceClient()

    try:
        profiles = list_profiles_table(c)
    except Exception as e:
        err = classify_error(e)
        err.print()
        return {"ok": False, "error": err.to_dict()}

    match = next((p for p in profiles if p.get("id") == profile_id), None)
    if match and match.get("status") in BUSY_STATUSES:
        err = StructuredError(
            ErrorCode.PROFILE_BUSY,
            message=f"Profile {profile_id} status is '{match.get('status')}'",
        )
        err.print()
        return {"ok": False, "error": err.to_dict()}

    if profiles and match is None:
        print(f"⚠️  Profile {profile_id} not in the list above — API may return 404.")

    print("⚠️  Deletion is permanent and cannot be undone.")
    print(f"    Target profile ID: {profile_id}")
    print()
    typed_id = input("Re-type the profile ID to delete: ").strip()
    if typed_id != profile_id:
        err = StructuredError(
            ErrorCode.DELETE_NOT_CONFIRMED,
            message=f"ID mismatch (got '{typed_id}')",
        )
        err.print()
        return {"ok": False, "error": err.to_dict()}

    yes = input("Type YES (uppercase) to confirm deletion: ").strip()
    if yes != "YES":
        err = StructuredError(ErrorCode.DELETE_CANCELLED, message="Confirmation was not YES")
        err.print()
        return {"ok": False, "error": err.to_dict()}

    print(f"\nWaiting {CONFIRM_DELAY_S}s before delete (Ctrl+C to abort)…")
    try:
        time.sleep(CONFIRM_DELAY_S)
    except KeyboardInterrupt:
        err = StructuredError(ErrorCode.DELETE_CANCELLED, message="Aborted during delay")
        err.print()
        return {"ok": False, "error": err.to_dict()}

    try:
        resp = c.delete_profile(profile_id, confirmed=True)
        if resp.get("ok"):
            print(f"✅ Profile {profile_id} deleted.")
            return {"ok": True, "profileId": profile_id}
        err = StructuredError(ErrorCode.DELETE_FAILED, message=str(resp))
        err.print()
        return {"ok": False, "error": err.to_dict()}
    except Exception as e:
        err = classify_error(e)
        body_msg = str(e).lower()
        status = getattr(getattr(e, "response", None), "status_code", None)
        if status == 409 or "before deleting" in body_msg:
            err = StructuredError(ErrorCode.PROFILE_BUSY, message=str(e), http_status=409)
        elif err.code == ErrorCode.UNEXPECTED_ERROR:
            err = StructuredError(ErrorCode.DELETE_FAILED, message=str(e))
        err.print()
        return {"ok": False, "error": err.to_dict()}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delete a Farmce profile (interactive confirmation required)"
    )
    parser.add_argument(
        "--profile-id",
        help="Profile ID to delete (if omitted, asked after listing)",
    )
    parser.add_argument("--json", action="store_true", help="Print result as JSON")
    args = parser.parse_args()

    tty_err = require_tty()
    if tty_err:
        if args.json:
            print(json.dumps({"ok": False, "error": tty_err.to_dict()}))
        return 1

    client = FarmceClient()
    profile_id = (args.profile_id or "").strip()

    if not profile_id:
        try:
            list_profiles_table(client)
        except Exception as e:
            classify_error(e).print()
            return 1
        profile_id = input("Enter profile ID to delete (or empty to cancel): ").strip()
        if not profile_id:
            err = StructuredError(ErrorCode.DELETE_CANCELLED, message="No profile ID entered")
            err.print()
            return 1

    result = confirm_and_delete(profile_id, client=client)
    if args.json:
        print(json.dumps(result))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
