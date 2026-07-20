#!/usr/bin/env python3
"""Session lifecycle helper: run → poll until running → return connectUrl.

Usage (CLI):
    python scripts/session_helper.py --profile-id <id>
    python scripts/session_helper.py --profile-id <id> --stop
    python scripts/session_helper.py --profile-id <id> --status

Usage (library):
    from scripts.session_helper import run_session, stop_session, get_session_status

    session = run_session("profile_id")
    if session:
        print(session["connectUrl"])
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

POLL_INTERVAL_S = 5
STARTUP_TIMEOUT_S = 120


def run_session(
    profile_id: str,
    client: FarmceClient = None,
    timeout_s: int = STARTUP_TIMEOUT_S,
    poll_interval_s: int = POLL_INTERVAL_S,
) -> Optional[dict]:
    """Start a session and poll until status is 'running'.

    Returns:
        dict with { profileId, sessionId, connectUrl } on success, or None on failure.
    """
    c = client or FarmceClient()

    print(f"\n🚀 Starting session for profile {profile_id}...")

    # Trigger start
    try:
        run_resp = c.run_session(profile_id)
    except Exception as e:
        classify_error(e).print()
        return None

    status = run_resp.get("data", {}).get("status", "")
    if status == "running":
        connect_url = run_resp.get("data", {}).get("url", "")
        session_id = run_resp.get("data", {}).get("session_id", "")
        print(f"✅ Session already running. connectUrl: {connect_url}")
        return {"profileId": profile_id, "sessionId": session_id, "connectUrl": connect_url}

    print(f"   Status: {status}. Polling until running (max {timeout_s}s)…")

    # Poll
    elapsed = 0
    while elapsed < timeout_s:
        time.sleep(poll_interval_s)
        elapsed += poll_interval_s

        try:
            status_resp = c.get_status(profile_id)
        except Exception as e:
            print(f"   ⚠️ Status poll error ({elapsed}s): {e}")
            continue

        current_status = status_resp.get("status", "unknown")
        connect_url = status_resp.get("url") or ""
        session_id = (status_resp.get("android") or {}).get("sessionId", "")

        print(f"   [{elapsed}s] status={current_status}", end="")
        if connect_url:
            print(f"  connectUrl ready", end="")
        print()

        if current_status == "running" and connect_url:
            print(f"\n✅ Session running!")
            print(f"   connectUrl: {connect_url}")
            return {"profileId": profile_id, "sessionId": session_id, "connectUrl": connect_url}

        if current_status == "error":
            StructuredError(
                ErrorCode.SESSION_START_FAILED,
                message="Session entered error state",
            ).print()
            return None

    StructuredError(
        ErrorCode.SESSION_START_TIMEOUT,
        message=f"Timeout after {timeout_s}s — session did not reach 'running'",
    ).print()
    return None


def stop_session(profile_id: str, client: FarmceClient = None) -> bool:
    """Stop an active session.

    Returns:
        True if stopped successfully, False otherwise.
    """
    c = client or FarmceClient()
    print(f"\n🛑 Stopping session for profile {profile_id}…")
    try:
        resp = c.stop_session(profile_id)
        if resp.get("ok"):
            print("✅ Session stopped.")
            return True
        StructuredError(ErrorCode.SESSION_STOP_FAILED, message=str(resp)).print()
        return False
    except Exception as e:
        classify_error(e).print()
        return False


def get_session_status(profile_id: str, client: FarmceClient = None) -> Optional[dict]:
    """Fetch current session status.

    Returns:
        dict with { status, connectUrl, sessionId } or None on error.
    """
    c = client or FarmceClient()
    try:
        resp = c.get_status(profile_id)
        return {
            "profileId": profile_id,
            "status": resp.get("status", "unknown"),
            "connectUrl": resp.get("url") or "",
            "sessionId": (resp.get("android") or {}).get("sessionId", ""),
        }
    except Exception as e:
        classify_error(e).print()
        return None


def _print_start_error(e: Exception) -> None:
    """Deprecated: use classify_error(e).print()."""
    classify_error(e).print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Farmce session lifecycle helper")
    parser.add_argument("--profile-id", required=True, help="Profile ID")
    parser.add_argument("--stop", action="store_true", help="Stop the session")
    parser.add_argument("--status", action="store_true", help="Get session status only")
    parser.add_argument("--timeout", type=int, default=STARTUP_TIMEOUT_S,
                        help=f"Max seconds to wait for startup (default: {STARTUP_TIMEOUT_S})")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    args = parser.parse_args()

    if args.stop:
        ok = stop_session(args.profile_id)
        if args.json:
            print(json.dumps({"ok": ok}))
        sys.exit(0 if ok else 1)

    if args.status:
        result = get_session_status(args.profile_id)
        if args.json:
            print(json.dumps(result))
        else:
            if result:
                print(f"status: {result['status']}")
                if result["connectUrl"]:
                    print(f"connectUrl: {result['connectUrl']}")
        sys.exit(0 if result else 1)

    session = run_session(args.profile_id, timeout_s=args.timeout)
    if args.json:
        print(json.dumps(session or {}))
    sys.exit(0 if session else 1)
