---
name: awesome-farmce-skill
description: Manage Farmce cloud Android devices for AI agent automation. Use when asked to start Android sessions, control profiles, manage proxies, take screenshots, or automate anything on a cloud phone via Farmce.
---

# Farmce Cloud Android Skill

> ⚠️ **IMPORTANT**: This skill controls real cloud Android devices that consume billeted time from your Farmce subscription. Always stop sessions when done.

**Configuration**: `assets/config.json` (auto-loads base URL and Bearer token)

---

> 🔒 **Security Notice**
>
> **Credential Handling:**
> - Your Bearer token is stored in `assets/config.json`
> - This file is protected by `.gitignore` — **never commit it**
> - Tokens auto-expire; run `init_config.py` again if you get 401 errors
> - **Never send your Bearer token in plain text in chat messages**
>
> **Autonomous Execution:**
> - Scripts call the Farmce REST API and can start/stop real cloud devices
> - **Always confirm destructive operations** (stop all sessions, delete profiles) with the user
> - Sessions auto-stop after ~45 minutes of inactivity on the server side

---

## First Time Setup

### 1. Install Python dependencies

```bash
# Recommended: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Run doctor to verify setup

```bash
python scripts/doctor.py
```

### 3. Initialize configuration (get Bearer token)

```bash
python scripts/init_config.py
```

This will:
1. Ask for your Farmce account email
2. Send a magic link to that email
3. Prompt you to open the link and paste back the Bearer token
4. Save `base_url` + `bearer_token` to `assets/config.json`

---

## Quick Start

#### List your devices and profiles

```python
from scripts.farmce_client import FarmceClient

client = FarmceClient()
devices = client.list_devices()
profiles = client.list_profiles()
```

Or via CLI:

```bash
python scripts/doctor.py
```

#### Start a session

```python
from scripts.session_helper import run_session

session = run_session("profile_id_here")
if session:
    print(f"connectUrl: {session['connectUrl']}")
```

Or via CLI:

```bash
python scripts/session_helper.py --profile-id <profile_id>
```

#### Take a screenshot

```bash
python scripts/screenshot.py --profile-id <profile_id>
```

---

## Core Workflow

### Step 1: Pre-check (limits & devices) ⭐⭐⭐

**Before starting a session, always check:**

```python
from scripts.farmce_client import FarmceClient

client = FarmceClient()

# Check user and limits
me = client.get_me()
usage = client.get_usage()

print(f"Plan: {me['data'].get('planName', 'no plan')}")
print(f"Minutes left: {usage['data'].get('minutesRemaining', 'N/A') if usage.get('data') else 'No active tariff'}")

# List devices
devices = client.list_devices()
for d in devices.get('allocations', []):
    print(f"  {d['id']} — status: {d['status']}")
```

If `minutesRemaining` is 0 or there is no active tariff, the session will be denied with 403.

### Step 2: List / create profiles

```python
# List existing profiles
profiles = client.list_profiles()
for p in profiles.get('profiles', []):
    print(f"  {p['id']} — {p['name']} ({p['status']})")

# Create a new profile
new_profile = client.create_profile("TikTok US", country_code="US")
profile_id = new_profile['data']['id']
```

### Step 3: Start session and get connectUrl

```python
from scripts.session_helper import run_session

# Starts the session and polls until status is "running"
session = run_session(profile_id)
if session:
    print(f"Session ready. connectUrl: {session['connectUrl']}")
    # Open the connectUrl in a browser to control the Android screen
```

`run_session()` handles:
- `POST /api/workspace/profiles/{id}/run`
- Polling `GET /api/workspace/profiles/{id}/status` until status = `running`
- Returning `{ profileId, sessionId, connectUrl }`

### Step 4: Screen control via connectUrl

Once you have `connectUrl`, open it in a browser-use tool or WebRTC-capable client.

Available controls through the player:
- **Tap** — click on any element
- **Swipe** — scroll, swipe gestures
- **Type** — keyboard input
- **Back / Home / Recents** — Android navigation buttons

For automated screen reading and element interaction, use the screenshot endpoint combined with a vision model to identify UI elements:

```python
from scripts.screenshot import take_screenshot

result = take_screenshot(profile_id)
# result['imageBase64'] — PNG image as base64
# result['imageUrl']   — or URL if provided
```

See `references/screen_control.md` for the full WebRTC workflow.

### Step 5: Stop the session

```python
client.stop_session(profile_id)
print("Session stopped.")
```

Always stop sessions when the task is done to preserve your quota.

---

## Session Management

### Session lifecycle

```
Profile → POST .../run → status: "starting" → status: "running" (connectUrl ready) → POST .../stop
```

- Sessions auto-stop after ~45 minutes without heartbeat (server-side)
- Quota is consumed from the time the session starts until it stops
- Maximum concurrent sessions depend on your plan

### Check session status

```python
status = client.get_status(profile_id)
print(f"status: {status['status']}, connectUrl: {status.get('url')}")
```

---

## Proxy Setup

```python
# Add a custom proxy
proxy = client.add_proxy(
    host="proxy.example.com",
    port="8080",
    login="user",
    password="pass",
    protocol="http"
)

# Check it works before attaching
check = client.check_proxy(
    host="proxy.example.com",
    port=8080,
    login="user",
    password="pass"
)
print(f"Proxy status: {check['status']}")  # "ok" or "fail"

# Attach to profile
client.update_profile(profile_id, proxy={"id": proxy['data']['id']})
```

See `examples/proxy-setup.md` for more.

---

## Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **Quota check** | Doctor checks remaining minutes before reporting readiness |
| **Session TTL** | Server auto-stops sessions idle for 45 minutes |
| **Endpoint boundary** | `FarmceClient.call()` uses a whitelist of allowed endpoints |
| **Credential safety** | `assets/config.json` in `.gitignore`; token not visible in API logs |
| **Stop on exit** | Wrap tasks with `try/finally: client.stop_session(profile_id)` |

---

## References

- `references/screen_control.md` — how to control the Android screen via connectUrl
- `references/error_codes.md` — error catalog with remediation steps
- `references/best_practices.md` — cost-saving and reliability tips
- `references/profiles_and_devices.md` — entities, model, and lifecycle
- Live OpenAPI spec: `https://app.farmce.com/api/openapi.json`
- Interactive docs: `https://app.farmce.com/api/swagger`

---

## Error Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| 401 | Invalid/expired token | Run `init_config.py` again |
| 403 `no_tariff` | No active subscription | Subscribe at app.farmce.com |
| 403 `quota_exhausted` | No minutes remaining | Upgrade plan or wait for reset |
| 409 `max_concurrent` | Too many active sessions | Stop another session first |
| 409 `profile_limit` | Profile count at plan max | Delete unused profiles |
| 502 | Android cloud start failed | Retry; if persistent, check server status |
| 501 `screenshot_not_supported` | Screenshot unavailable in this mode | Use connectUrl player instead |

See `references/error_codes.md` for the full catalog.
