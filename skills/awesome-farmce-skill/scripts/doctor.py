#!/usr/bin/env python3
"""Farmce Skill — Doctor Diagnostic Tool.

Checks all dependencies and services before running cloud Android operations.

Usage:
    python scripts/doctor.py
    python scripts/doctor.py --profile-id <profile_id>
    python scripts/doctor.py --json
"""

import sys
import os
import json
import time
import argparse
from typing import List, Optional

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scripts.error_codes import ErrorCode


class DiagStatus:
    OK = "OK"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


class DiagResult:
    def __init__(self, name: str, status: str, message: str, error_code: str = None):
        self.name = name
        self.status = status
        self.message = message
        self.error_code = error_code

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "error_code": self.error_code,
        }

    def icon(self) -> str:
        return {"OK": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}.get(self.status, "?")


# ── Checks ────────────────────────────────────────────────────────────────────

def check_python_deps() -> List[DiagResult]:
    results = []
    try:
        import requests
        results.append(DiagResult("requests", DiagStatus.OK, f"requests {requests.__version__} installed"))
    except ImportError:
        results.append(DiagResult(
            "requests", DiagStatus.FAIL,
            "requests not installed. Run: pip install requests",
            ErrorCode.ENV_DEPENDENCY_MISSING,
        ))
    return results


def check_config() -> List[DiagResult]:
    try:
        from scripts.utils import load_config
        cfg = load_config()
        base_url = cfg.get("base_url", "")
        token_preview = cfg.get("bearer_token", "")[:8] + "…" if cfg.get("bearer_token") else "(empty)"
        return [DiagResult(
            "config", DiagStatus.OK,
            f"Loaded. base_url={base_url}, token={token_preview}",
        )]
    except FileNotFoundError as e:
        return [DiagResult("config", DiagStatus.FAIL, str(e), ErrorCode.CONFIG_MISSING)]
    except ValueError as e:
        return [DiagResult("config", DiagStatus.FAIL, str(e), ErrorCode.CONFIG_INVALID)]
    except Exception as e:
        return [DiagResult("config", DiagStatus.FAIL, f"Unexpected error: {e}", ErrorCode.UNEXPECTED_ERROR)]


def check_network(base_url: str) -> List[DiagResult]:
    import requests as req
    try:
        start = time.time()
        resp = req.get(f"{base_url}/health", timeout=10)
        elapsed = time.time() - start
        if resp.status_code < 500:
            return [DiagResult(
                "network", DiagStatus.OK,
                f"Reached {base_url} in {elapsed:.2f}s (HTTP {resp.status_code})",
            )]
        return [DiagResult(
            "network", DiagStatus.WARN,
            f"Server responded with HTTP {resp.status_code} in {elapsed:.2f}s",
        )]
    except req.exceptions.Timeout:
        return [DiagResult(
            "network", DiagStatus.FAIL,
            f"Timeout connecting to {base_url}",
            ErrorCode.NETWORK_TIMEOUT,
        )]
    except req.exceptions.ConnectionError as e:
        return [DiagResult(
            "network", DiagStatus.FAIL,
            f"Cannot connect to {base_url}: {e}",
            ErrorCode.NETWORK_UNREACHABLE,
        )]
    except Exception as e:
        return [DiagResult(
            "network", DiagStatus.FAIL,
            f"Network error: {e}",
            ErrorCode.NETWORK_UNREACHABLE,
        )]


def check_auth(client) -> List[DiagResult]:
    try:
        me = client.get_me()
        email = me.get("email") or me.get("user", {}).get("email", "unknown")
        plan = me.get("planName") or "(no plan)"
        return [DiagResult("auth", DiagStatus.OK, f"Authenticated as {email}, plan: {plan}")]
    except Exception as e:
        status_code = getattr(getattr(e, "response", None), "status_code", None)
        if status_code == 401:
            return [DiagResult(
                "auth", DiagStatus.FAIL,
                "401 Unauthorized — token is invalid or expired. Run: python scripts/init_config.py",
                ErrorCode.AUTH_UNAUTHORIZED,
            )]
        return [DiagResult(
            "auth", DiagStatus.FAIL,
            f"Auth check failed: {e}",
            ErrorCode.AUTH_UNAUTHORIZED,
        )]


def check_limits(client) -> List[DiagResult]:
    results = []
    try:
        usage = client.get_usage()
        data = usage.get("data") if isinstance(usage.get("data"), dict) else usage
        if not data:
            results.append(DiagResult(
                "limits", DiagStatus.WARN,
                "No active tariff. Subscribe at https://app.farmce.com to start sessions.",
                ErrorCode.NO_TARIFF,
            ))
            return results

        minutes = data.get("minutesRemaining")
        concurrent = data.get("maxConcurrentSessions")
        active = data.get("activeSessions", 0)

        if minutes is not None and minutes <= 0:
            results.append(DiagResult(
                "quota", DiagStatus.WARN,
                f"Quota exhausted: 0 minutes remaining. Upgrade plan to continue.",
                ErrorCode.QUOTA_EXHAUSTED,
            ))
        else:
            remaining_str = f"{minutes} min remaining" if minutes is not None else "unlimited"
            results.append(DiagResult("quota", DiagStatus.OK, remaining_str))

        if concurrent is not None:
            results.append(DiagResult(
                "concurrent_sessions", DiagStatus.OK,
                f"Active sessions: {active}/{concurrent}",
            ))
    except Exception as e:
        results.append(DiagResult("limits", DiagStatus.WARN, f"Could not fetch usage: {e}"))
    return results


def check_devices(client) -> List[DiagResult]:
    try:
        resp = client.list_devices()
        allocations = resp.get("allocations", [])
        if not allocations:
            return [DiagResult(
                "devices", DiagStatus.WARN,
                "No cloud phones found. Rent a device at https://app.farmce.com.",
            )]
        active = [a for a in allocations if a.get("status") == "active"]
        return [DiagResult(
            "devices", DiagStatus.OK,
            f"{len(allocations)} device(s) found, {len(active)} active.",
        )]
    except Exception as e:
        return [DiagResult("devices", DiagStatus.WARN, f"Could not list devices: {e}")]


def check_profiles(client) -> List[DiagResult]:
    try:
        resp = client.list_profiles()
        profiles = resp.get("profiles", [])
        limits = resp.get("limits", {})
        max_p = limits.get("maxProfiles")
        running = [p for p in profiles if p.get("status") == "running"]
        limit_str = f"/{max_p}" if max_p is not None else ""
        return [DiagResult(
            "profiles", DiagStatus.OK,
            f"{len(profiles)}{limit_str} profiles, {len(running)} running.",
        )]
    except Exception as e:
        return [DiagResult("profiles", DiagStatus.WARN, f"Could not list profiles: {e}")]


def check_profile_status(client, profile_id: str) -> List[DiagResult]:
    try:
        status = client.get_status(profile_id)
        s = status.get("status", "unknown")
        url = status.get("url") or status.get("connectUrl", "")
        msg = f"Profile {profile_id}: status={s}"
        if url:
            msg += f", connectUrl available"
        return [DiagResult("profile_status", DiagStatus.OK, msg)]
    except Exception as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        if code == 404:
            return [DiagResult(
                "profile_status", DiagStatus.FAIL,
                f"Profile {profile_id} not found.",
                "PROFILE_NOT_FOUND",
            )]
        return [DiagResult("profile_status", DiagStatus.FAIL, f"Status check failed: {e}")]


# ── Runner ────────────────────────────────────────────────────────────────────

def run_doctor(profile_id: Optional[str] = None) -> dict:
    all_results: List[DiagResult] = []

    print("=" * 65)
    print("  Farmce Skill — Doctor Diagnostic")
    print("=" * 65)

    print("\n📦 Phase 1: Python dependencies")
    print("-" * 65)
    dep_results = check_python_deps()
    all_results.extend(dep_results)
    for r in dep_results:
        print(f"  {r.icon()} {r.name}: {r.message}")

    if any(r.status == DiagStatus.FAIL for r in dep_results):
        print("\n❌ Install missing dependencies before proceeding.")
        return _summary(all_results)

    print("\n⚙️  Phase 2: Configuration")
    print("-" * 65)
    cfg_results = check_config()
    all_results.extend(cfg_results)
    for r in cfg_results:
        print(f"  {r.icon()} {r.name}: {r.message}")

    if any(r.status == DiagStatus.FAIL for r in cfg_results):
        print("\n❌ Fix config before proceeding (see above).")
        return _summary(all_results)

    from scripts.utils import get_base_url
    from scripts.farmce_client import FarmceClient

    base_url = get_base_url()
    client = FarmceClient()

    print(f"\n🌐 Phase 3: Network ({base_url})")
    print("-" * 65)
    net_results = check_network(base_url)
    all_results.extend(net_results)
    for r in net_results:
        print(f"  {r.icon()} {r.name}: {r.message}")

    print("\n🔑 Phase 4: Authentication")
    print("-" * 65)
    auth_results = check_auth(client)
    all_results.extend(auth_results)
    for r in auth_results:
        print(f"  {r.icon()} {r.name}: {r.message}")

    if any(r.status == DiagStatus.FAIL for r in auth_results):
        return _summary(all_results)

    print("\n📊 Phase 5: Limits & quota")
    print("-" * 65)
    limit_results = check_limits(client)
    all_results.extend(limit_results)
    for r in limit_results:
        print(f"  {r.icon()} {r.name}: {r.message}")

    print("\n📱 Phase 6: Devices & profiles")
    print("-" * 65)
    device_results = check_devices(client) + check_profiles(client)
    all_results.extend(device_results)
    for r in device_results:
        print(f"  {r.icon()} {r.name}: {r.message}")

    if profile_id:
        print(f"\n🔍 Phase 7: Profile status ({profile_id})")
        print("-" * 65)
        p_results = check_profile_status(client, profile_id)
        all_results.extend(p_results)
        for r in p_results:
            print(f"  {r.icon()} {r.name}: {r.message}")

    return _summary(all_results)


def _summary(all_results: List[DiagResult]) -> dict:
    ok = sum(1 for r in all_results if r.status == DiagStatus.OK)
    warn = sum(1 for r in all_results if r.status == DiagStatus.WARN)
    fail = sum(1 for r in all_results if r.status == DiagStatus.FAIL)
    skip = sum(1 for r in all_results if r.status == DiagStatus.SKIP)

    print("\n" + "=" * 65)
    print("  Summary")
    print("=" * 65)
    print(f"  ✅ OK:      {ok}")
    print(f"  ⚠️  WARN:   {warn}")
    print(f"  ❌ FAILED:  {fail}")
    print(f"  ⏭️  SKIP:   {skip}")

    failed = [r for r in all_results if r.status == DiagStatus.FAIL and r.error_code]
    if failed:
        print("\n🔴 Errors:")
        for r in failed:
            print(f"  {r.error_code}: {r.name} — {r.message}")

    print()
    return {
        "results": [r.to_dict() for r in all_results],
        "summary": {"ok": ok, "warn": warn, "failed": fail, "skip": skip, "total": len(all_results)},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Farmce Skill Doctor")
    parser.add_argument("--profile-id", help="Check specific profile status")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    result = run_doctor(profile_id=args.profile_id)

    if args.json:
        print(json.dumps(result, indent=2))

    sys.exit(1 if result["summary"]["failed"] > 0 else 0)
