# Error Codes

All errors returned by the Farmce Public API follow a consistent structure:

```json
{
  "error": "error_code_string",
  "message": "Human-readable description"
}
```

HTTP status codes map to error categories.

---

## HTTP 400 — Bad Request

| Error | Cause | Fix |
|-------|-------|-----|
| `email_required` | Missing email in magic-link request | Provide `email` in request body |
| `host_port_required` | Missing host/port in proxy check | Provide both `host` and `port` |

---

## HTTP 401 — Unauthorized

| Error | Cause | Fix |
|-------|-------|-----|
| (any) | Missing, expired, or invalid Bearer token | Run `python scripts/init_config.py` to get a new token |

Tokens from magic link do not expire on a fixed timer but can be invalidated by the server (session termination, re-login). If you get 401, always refresh via `init_config.py`.

---

## HTTP 403 — Forbidden

| Error | Cause | Fix |
|-------|-------|-----|
| `no_tariff` | No active subscription | Subscribe at https://app.farmce.com/pricing |
| `quota_exhausted` | Device minutes for the billing period are used up | Upgrade plan or wait for next billing cycle |
| `plan_upgrade_required` | Feature not available on current plan | Upgrade at https://app.farmce.com/pricing |

**Check before starting a session:**

```python
usage = client.get_usage()
data = usage.get("data")
if not data:
    print("No tariff")
elif data.get("minutesRemaining", 1) <= 0:
    print("Quota exhausted")
```

---

## HTTP 404 — Not Found

| Error | Cause | Fix |
|-------|-------|-----|
| (profile not found) | Profile ID does not exist for this user | List profiles with `GET /api/workspace/profiles` |
| (allocation not found) | Device allocation ID is wrong or expired | List devices with `GET /api/phones/allocations` |

---

## HTTP 409 — Conflict

| Error | Cause | Fix |
|-------|-------|-----|
| `max_concurrent_sessions` | Active session count equals plan limit | Stop another session first |
| `profile_limit_reached` | Profile count equals plan maximum | Delete unused profiles |
| `active_session_required` | Screenshot called without a running session | Start a session first with `POST .../run` |

---

## HTTP 501 — Not Implemented

| Error | Cause | Fix |
|-------|-------|-----|
| `screenshot_not_supported_in_vmos_direct_mode` | Screenshot endpoint not available in this backend configuration | Use the connectUrl WebRTC player; take a screenshot in the browser instead |

---

## HTTP 502 — Bad Gateway

| Error | Cause | Fix |
|-------|-------|-----|
| `android_cloud_start_failed` | Upstream Android cloud provider failed to start the instance | Wait 30s and retry; if persistent, contact Farmce support |
| `vmos_client_error` | Internal VMOS service error | Retry; check service status |
| `upstream_unavailable` | Proxy service or phone service unavailable | Retry; if persistent, contact support |

---

## Client-side errors (scripts)

| Error class | Cause | Fix |
|-------------|-------|-----|
| `FileNotFoundError` in `utils.py` | `assets/config.json` missing | Run `python scripts/init_config.py` |
| `ValueError: bearer_token is not set` | Token placeholder in config | Run `python scripts/init_config.py` |
| `FarmceForbiddenError` (endpoint whitelist) | Called an undocumented endpoint | Only use endpoints listed in `farmce_client.py`; check SKILL.md |
| `FarmceForbiddenError` (delete) | `delete_profile` without `confirmed=True` | Use `python scripts/delete_helper.py` |
| `requests.HTTPError` | HTTP error from API | Check status code; see table above |
| `requests.ConnectionError` | Cannot reach backend | Check network; verify `base_url` in `assets/config.json` |
| `requests.Timeout` | Backend too slow | Retry; check `doctor.py` for network latency |

---

## Structured script codes (`scripts/error_codes.py`)

Scripts emit machine-readable codes via `classify_error()` / `classify_http_error()`:

| Code | When | Fix |
|------|------|-----|
| `ENV_DEPENDENCY_MISSING` | `requests` (etc.) not installed | `pip install -r requirements.txt` |
| `CONFIG_MISSING` / `CONFIG_INVALID` | No or empty token | `init_config.py` |
| `NETWORK_UNREACHABLE` / `NETWORK_TIMEOUT` | API unreachable | Check network / `base_url` |
| `AUTH_UNAUTHORIZED` | 401 | `init_config.py` |
| `NO_TARIFF` / `QUOTA_EXHAUSTED` | Billing | Subscribe / upgrade |
| `SESSION_START_TIMEOUT` / `SESSION_START_FAILED` | Boot failed | Retry; doctor |
| `PROFILE_BUSY` | Delete while running | Stop session first |
| `DELETE_REQUIRES_TTY` | Non-interactive delete | Run helper in a real terminal |
| `DELETE_NOT_CONFIRMED` / `DELETE_CANCELLED` | User did not confirm | Re-run and type ID + `YES` |
| `ENDPOINT_FORBIDDEN` | Whitelist / unconfirmed delete | Use documented helpers |

```python
from scripts.error_codes import classify_error

try:
    client.run_session(profile_id)
except Exception as e:
    err = classify_error(e)
    print(err.to_dict())  # { code, message, recommendation, severity, ... }
```

---

## Remediation quick reference

```
401 Unauthorized         → python scripts/init_config.py
403 no_tariff            → subscribe at https://app.farmce.com
403 quota_exhausted      → upgrade plan
409 max_concurrent       → client.stop_session(other_profile_id)
409 profile busy/delete  → stop session, then delete_helper.py
404 profile not found    → client.list_profiles() to get valid IDs
501 screenshot           → use connectUrl player (see references/screen_control.md)
502 any                  → wait 30s and retry
```
