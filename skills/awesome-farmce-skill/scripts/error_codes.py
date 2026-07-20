#!/usr/bin/env python3
"""Farmce Skill — structured error codes for scripts and agents.

Usage:
    from scripts.error_codes import ErrorCode, StructuredError, classify_error, classify_http_error

    err = classify_error(exc)
    print(err.to_dict())

    # Or from an HTTP response:
    err = classify_http_error(status_code, body)
"""

from typing import Any, Optional


class ErrorCode:
    # Environment & config
    ENV_DEPENDENCY_MISSING = "ENV_DEPENDENCY_MISSING"
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"

    # Network
    NETWORK_UNREACHABLE = "NETWORK_UNREACHABLE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"

    # Auth & billing
    AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
    NO_TARIFF = "NO_TARIFF"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"
    PLAN_UPGRADE_REQUIRED = "PLAN_UPGRADE_REQUIRED"

    # Profiles & sessions
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    PROFILE_LIMIT_REACHED = "PROFILE_LIMIT_REACHED"
    PROFILE_BUSY = "PROFILE_BUSY"
    MAX_CONCURRENT_SESSIONS = "MAX_CONCURRENT_SESSIONS"
    SESSION_START_TIMEOUT = "SESSION_START_TIMEOUT"
    SESSION_START_FAILED = "SESSION_START_FAILED"
    ACTIVE_SESSION_REQUIRED = "ACTIVE_SESSION_REQUIRED"
    SESSION_STOP_FAILED = "SESSION_STOP_FAILED"

    # Screenshot / screen
    SCREENSHOT_NOT_SUPPORTED = "SCREENSHOT_NOT_SUPPORTED"

    # Delete safeguards
    DELETE_NOT_CONFIRMED = "DELETE_NOT_CONFIRMED"
    DELETE_REQUIRES_TTY = "DELETE_REQUIRES_TTY"
    DELETE_CANCELLED = "DELETE_CANCELLED"
    DELETE_FAILED = "DELETE_FAILED"

    # Client / API
    ENDPOINT_FORBIDDEN = "ENDPOINT_FORBIDDEN"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"


ERROR_METADATA = {
    ErrorCode.ENV_DEPENDENCY_MISSING: {
        "description": "Required Python package is missing",
        "recommendation": "pip install -r requirements.txt  (use a venv)",
        "severity": "critical",
    },
    ErrorCode.CONFIG_MISSING: {
        "description": "assets/config.json not found",
        "recommendation": "python scripts/init_config.py",
        "severity": "critical",
    },
    ErrorCode.CONFIG_INVALID: {
        "description": "bearer_token missing or still a placeholder",
        "recommendation": "python scripts/init_config.py",
        "severity": "critical",
    },
    ErrorCode.NETWORK_UNREACHABLE: {
        "description": "Cannot reach Farmce API",
        "recommendation": "Check network and base_url in assets/config.json; run doctor.py",
        "severity": "critical",
    },
    ErrorCode.NETWORK_TIMEOUT: {
        "description": "API request timed out",
        "recommendation": "Retry; run doctor.py to check latency",
        "severity": "warning",
    },
    ErrorCode.AUTH_UNAUTHORIZED: {
        "description": "Missing, invalid, or expired Bearer token",
        "recommendation": "python scripts/init_config.py",
        "severity": "critical",
    },
    ErrorCode.NO_TARIFF: {
        "description": "No active subscription",
        "recommendation": "Subscribe at https://app.farmce.com/pricing",
        "severity": "critical",
    },
    ErrorCode.QUOTA_EXHAUSTED: {
        "description": "No device minutes remaining",
        "recommendation": "Upgrade plan or wait for the next billing cycle",
        "severity": "critical",
    },
    ErrorCode.PLAN_UPGRADE_REQUIRED: {
        "description": "Feature not available on current plan",
        "recommendation": "Upgrade at https://app.farmce.com/pricing",
        "severity": "critical",
    },
    ErrorCode.PROFILE_NOT_FOUND: {
        "description": "Profile ID not found for this user",
        "recommendation": "List profiles: client.list_profiles()",
        "severity": "warning",
    },
    ErrorCode.PROFILE_LIMIT_REACHED: {
        "description": "Profile count at plan maximum",
        "recommendation": "Delete unused profiles via scripts/delete_helper.py",
        "severity": "warning",
    },
    ErrorCode.PROFILE_BUSY: {
        "description": "Profile is running/starting — cannot delete",
        "recommendation": "Stop the session first: python scripts/session_helper.py --profile-id <id> --stop",
        "severity": "warning",
    },
    ErrorCode.MAX_CONCURRENT_SESSIONS: {
        "description": "Too many active sessions for this plan",
        "recommendation": "Stop another session first",
        "severity": "warning",
    },
    ErrorCode.SESSION_START_TIMEOUT: {
        "description": "Session did not reach running within timeout",
        "recommendation": "Retry; check quota and doctor.py; if persistent contact support",
        "severity": "warning",
    },
    ErrorCode.SESSION_START_FAILED: {
        "description": "Android cloud failed to start the instance",
        "recommendation": "Wait 30s and retry; check server status",
        "severity": "warning",
    },
    ErrorCode.ACTIVE_SESSION_REQUIRED: {
        "description": "Screenshot/action needs a running session",
        "recommendation": "Start with session_helper.py --profile-id <id>",
        "severity": "warning",
    },
    ErrorCode.SESSION_STOP_FAILED: {
        "description": "Failed to stop the session",
        "recommendation": "Retry stop; check status; sweeper may stop after ~10 min without heartbeat",
        "severity": "warning",
    },
    ErrorCode.SCREENSHOT_NOT_SUPPORTED: {
        "description": "Screenshot REST not available in this backend mode",
        "recommendation": "Open connectUrl and capture the player in the browser",
        "severity": "warning",
    },
    ErrorCode.DELETE_NOT_CONFIRMED: {
        "description": "Delete blocked: confirmation missing",
        "recommendation": "Run: python scripts/delete_helper.py  and type the profile ID + YES",
        "severity": "critical",
    },
    ErrorCode.DELETE_REQUIRES_TTY: {
        "description": "Delete blocked: not an interactive terminal",
        "recommendation": "Run delete_helper.py manually in a real terminal (agents must not auto-fill YES)",
        "severity": "critical",
    },
    ErrorCode.DELETE_CANCELLED: {
        "description": "User cancelled deletion",
        "recommendation": "No action needed",
        "severity": "info",
    },
    ErrorCode.DELETE_FAILED: {
        "description": "Profile delete API call failed",
        "recommendation": "Check profile status (must be stopped); verify ID; retry",
        "severity": "warning",
    },
    ErrorCode.ENDPOINT_FORBIDDEN: {
        "description": "Endpoint not in FarmceClient whitelist",
        "recommendation": "Use only documented methods; see SKILL.md / swagger",
        "severity": "critical",
    },
    ErrorCode.UPSTREAM_UNAVAILABLE: {
        "description": "Upstream phone/proxy service unavailable",
        "recommendation": "Retry; if persistent contact support",
        "severity": "warning",
    },
    ErrorCode.UNEXPECTED_ERROR: {
        "description": "Unexpected error",
        "recommendation": "Run doctor.py; review the message; retry",
        "severity": "error",
    },
}


# Map API `error` field → ErrorCode
_API_ERROR_MAP = {
    "no_tariff": ErrorCode.NO_TARIFF,
    "quota_exhausted": ErrorCode.QUOTA_EXHAUSTED,
    "plan_upgrade_required": ErrorCode.PLAN_UPGRADE_REQUIRED,
    "max_concurrent_sessions": ErrorCode.MAX_CONCURRENT_SESSIONS,
    "profile_limit_reached": ErrorCode.PROFILE_LIMIT_REACHED,
    "active_session_required": ErrorCode.ACTIVE_SESSION_REQUIRED,
    "screenshot_not_supported_in_vmos_direct_mode": ErrorCode.SCREENSHOT_NOT_SUPPORTED,
    "android_cloud_start_failed": ErrorCode.SESSION_START_FAILED,
    "vmos_client_error": ErrorCode.SESSION_START_FAILED,
    "upstream_unavailable": ErrorCode.UPSTREAM_UNAVAILABLE,
    "profile_update_failed": ErrorCode.UNEXPECTED_ERROR,
}


class StructuredError:
    def __init__(
        self,
        code: str,
        message: str = None,
        recommendation: str = None,
        http_status: int = None,
        details: Any = None,
    ):
        meta = ERROR_METADATA.get(code, {})
        self.code = code
        self.message = message or meta.get("description", "")
        self.recommendation = recommendation or meta.get("recommendation", "")
        self.severity = meta.get("severity", "error")
        self.http_status = http_status
        self.details = details

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.recommendation:
            parts.append(f"Fix: {self.recommendation}")
        return "\n".join(parts)

    def to_dict(self) -> dict:
        out = {
            "code": self.code,
            "message": self.message,
            "recommendation": self.recommendation,
            "severity": self.severity,
        }
        if self.http_status is not None:
            out["http_status"] = self.http_status
        if self.details is not None:
            out["details"] = self.details
        return out

    def print(self) -> None:
        icon = {"critical": "❌", "warning": "⚠️", "error": "❌", "info": "ℹ️"}.get(
            self.severity, "❌"
        )
        print(f"{icon} [{self.code}] {self.message}")
        if self.recommendation:
            print(f"   → {self.recommendation}")


def make_error(code: str, message: str = None, **kwargs) -> StructuredError:
    return StructuredError(code, message=message, **kwargs)


def classify_http_error(status_code: int, body: Any = None) -> StructuredError:
    """Map HTTP status + API JSON body to a StructuredError."""
    error_key = ""
    message = None
    if isinstance(body, dict):
        error_key = str(body.get("error") or "")
        message = body.get("message") or error_key or None
    elif isinstance(body, str) and body.strip():
        message = body.strip()[:300]

    if error_key in _API_ERROR_MAP:
        return StructuredError(
            _API_ERROR_MAP[error_key],
            message=message,
            http_status=status_code,
            details=body if isinstance(body, dict) else None,
        )

    # Fuzzy match on error string
    lowered = (error_key + " " + (message or "")).lower()
    if "stop the profile" in lowered or "before deleting" in lowered:
        return StructuredError(
            ErrorCode.PROFILE_BUSY, message=message, http_status=status_code, details=body
        )
    if "quota" in lowered:
        return StructuredError(
            ErrorCode.QUOTA_EXHAUSTED, message=message, http_status=status_code, details=body
        )
    if "tariff" in lowered or "no_plan" in lowered:
        return StructuredError(
            ErrorCode.NO_TARIFF, message=message, http_status=status_code, details=body
        )
    if "not found" in lowered:
        return StructuredError(
            ErrorCode.PROFILE_NOT_FOUND, message=message, http_status=status_code, details=body
        )

    if status_code == 401:
        return StructuredError(ErrorCode.AUTH_UNAUTHORIZED, message=message, http_status=401)
    if status_code == 403:
        return StructuredError(ErrorCode.NO_TARIFF, message=message, http_status=403, details=body)
    if status_code == 404:
        return StructuredError(
            ErrorCode.PROFILE_NOT_FOUND, message=message, http_status=404, details=body
        )
    if status_code == 409:
        return StructuredError(
            ErrorCode.MAX_CONCURRENT_SESSIONS, message=message, http_status=409, details=body
        )
    if status_code == 501:
        return StructuredError(
            ErrorCode.SCREENSHOT_NOT_SUPPORTED, message=message, http_status=501, details=body
        )
    if status_code in (502, 503):
        return StructuredError(
            ErrorCode.UPSTREAM_UNAVAILABLE, message=message, http_status=status_code, details=body
        )

    return StructuredError(
        ErrorCode.UNEXPECTED_ERROR,
        message=message or f"HTTP {status_code}",
        http_status=status_code,
        details=body,
    )


def classify_error(exception: Exception) -> StructuredError:
    """Classify a Python exception into a StructuredError."""
    error_type = type(exception).__name__
    msg = str(exception)

    if error_type in ("ImportError", "ModuleNotFoundError"):
        return StructuredError(ErrorCode.ENV_DEPENDENCY_MISSING, msg)

    if error_type == "FileNotFoundError":
        return StructuredError(ErrorCode.CONFIG_MISSING, msg)

    if error_type == "ValueError" and "bearer_token" in msg.lower():
        return StructuredError(ErrorCode.CONFIG_INVALID, msg)

    if error_type == "FarmceForbiddenError":
        return StructuredError(ErrorCode.ENDPOINT_FORBIDDEN, msg)

    # requests HTTPError
    resp = getattr(exception, "response", None)
    if resp is not None:
        try:
            body = resp.json()
        except Exception:
            body = getattr(resp, "text", None)
        return classify_http_error(resp.status_code, body)

    lowered = msg.lower()
    if "timeout" in lowered or error_type == "TimeoutError":
        return StructuredError(ErrorCode.NETWORK_TIMEOUT, msg)
    if "connection" in lowered or error_type == "ConnectionError":
        return StructuredError(ErrorCode.NETWORK_UNREACHABLE, msg)

    return StructuredError(ErrorCode.UNEXPECTED_ERROR, msg)


if __name__ == "__main__":
    samples = [
        classify_http_error(401, {"error": "unauthorized"}),
        classify_http_error(403, {"error": "quota_exhausted"}),
        classify_http_error(409, {"error": "Stop the profile before deleting"}),
        classify_error(FileNotFoundError("Config not found")),
    ]
    for err in samples:
        err.print()
        print()
