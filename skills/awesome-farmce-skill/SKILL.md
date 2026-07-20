---
name: awesome-farmce-skill
description: Beta skill for Farmce cloud Android via REST API + WebRTC connectUrl (no ADB). Use when asked to list/start/stop profiles, manage proxies, or take screenshots. Prefer documented scenarios; ask when unclear; do not invent extra steps.
---

# Farmce Cloud Android Skill

> ⚠️ **BETA**: For AI agents against real Farmce devices. Prefer `examples/`. Always stop sessions when done — they consume billed minutes. Do not run unattended until you have validated the flows yourself.

**Configuration**: `assets/config.json` (auto-loads base URL and Bearer token)

---

> 🔒 **Security Notice**
>
> **Scope (API only):**
> - Supported: Farmce REST API, session `connectUrl` (WebRTC player), REST screenshots, proxies
> - **Not supported:** local `adb`, device serial workflows, on-device UI automation libraries, shell-on-device, built-in social RPA packs
> - Do not invent ADB/serial steps — they are outside this skill
>
> **Credential Handling:**
> - Your Bearer token is stored in `assets/config.json`
> - This file is protected by `.gitignore` — **never commit it**
> - Tokens auto-expire; run `init_config.py` again if you get 401 errors
> - **Never send your Bearer token in plain text in chat messages**
>
> **Autonomous Execution:**
> - Scripts call the Farmce REST API and can start/stop real cloud devices
> - Validate behavior before leaving the agent unsupervised
> - **Always confirm destructive operations** (stop all sessions, delete profiles) with the user
> - **Never call `delete_profile` directly** — use `scripts/delete_helper.py` (interactive YES)
> - Sessions auto-stop after ~10 minutes without player heartbeat (server-side)

---

## Agent Execution Rules (MANDATORY)

**Critical directives for AI agents:**

1. **Do only what the user asked.** Do not create profiles, start sessions, attach proxies, or stop devices "just in case" or as a side quest.
2. **Ask when unclear.** If profile ID/name, target device, or next step is ambiguous — ask the user. Do not guess or invent parameters.
3. **No local device tooling.** Only REST via `FarmceClient`, `session_helper`, `screenshot`, and screen control via `connectUrl`. Stay within the endpoint whitelist.
4. **Confirm before costly or destructive actions.** Before `run` (billed minutes), `stop all`, or delete — confirm the exact profile/action with the user unless they already gave an explicit instruction for that ID.
5. **Prefer documented scenarios.** Follow `examples/start-session.md`, `examples/proxy-setup.md`, and the Core Workflow below. Do not invent multi-step automations beyond the API surface.
6. **No auto-login / no “logical” setup.** Do not log into apps, change system settings, install apps, or accept dialogs unless the user explicitly asked. If a login/onboarding wall appears — stop and ask. See `references/screen_control.md`.
7. **Stop what you start.** If you started a session, stop it when the task is done (or remind the user). Wrap work in `try/finally` when scripting.
8. **Deletion only via `delete_helper.py`.** Never bypass confirmation; never auto-fill `YES`.
9. **Credentials stay local.** Never print full Bearer tokens or proxy passwords; mask in logs/output.

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

- Sessions auto-stop after ~10 minutes without player heartbeat (server-side). Keep `connectUrl` open so the player can ping; clicks alone do not count as heartbeat.
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
| **Session TTL** | Server auto-stops the phone ~10 minutes after the last player heartbeat |
| **Endpoint boundary** | `FarmceClient` uses a whitelist of allowed endpoints |
| **Credential safety** | `assets/config.json` in `.gitignore`; token not visible in API logs |
| **Stop on exit** | Wrap tasks with `try/finally: client.stop_session(profile_id)` |
| **Deletion safeguards** | `delete_helper.py`: TTY required, re-type profile ID + `YES`, delay; `delete_profile(confirmed=False)` is blocked |
| **Structured errors** | `scripts/error_codes.py` — codes + recommendations for agents |

---

## Deletion Workflow (MANDATORY)

AI agents **MUST NOT** call `client.delete_profile()` directly. Follow this sequence:

1. List profiles and show ID / name / status to the user  
2. Ask which ID to delete and require an explicit reply containing the ID and `YES`  
3. **STOP AND WAIT** for the user — do not auto-fill confirmation  
4. Instruct the user (or run in their interactive terminal):

```bash
python scripts/delete_helper.py --profile-id <id>
```

The script re-asks for the ID, requires typing `YES`, waits 3 seconds, then deletes.  
Profile must be **stopped** first (API returns 409 `PROFILE_BUSY` otherwise).

> If you cannot wait for interactive confirmation, do not delete. Tell the user to run `delete_helper.py` manually.

---

## References

- `references/screen_control.md` — how to control the Android screen via connectUrl
- `references/error_codes.md` — error catalog with remediation steps
- `scripts/error_codes.py` — structured codes used by scripts (`classify_error`, `classify_http_error`)
- `references/best_practices.md` — cost-saving and reliability tips
- `references/profiles_and_devices.md` — entities, model, and lifecycle
- Live OpenAPI spec: `https://app.farmce.com/api/openapi.json`
- Interactive docs: `https://app.farmce.com/api/swagger`

---

## Error Quick Reference

| Error | Cause | Fix |
|-------|-------|-----|
| 401 / `AUTH_UNAUTHORIZED` | Invalid/expired token | Run `init_config.py` again |
| 403 `NO_TARIFF` | No active subscription | Subscribe at app.farmce.com |
| 403 `QUOTA_EXHAUSTED` | No minutes remaining | Upgrade plan or wait for reset |
| 409 `MAX_CONCURRENT_SESSIONS` | Too many active sessions | Stop another session first |
| 409 `PROFILE_LIMIT_REACHED` | Profile count at plan max | Delete via `delete_helper.py` |
| 409 `PROFILE_BUSY` | Delete while session active | Stop session first |
| `SESSION_START_TIMEOUT` | Boot took too long | Retry; check doctor |
| 502 / `UPSTREAM_UNAVAILABLE` | Android cloud start failed | Retry; if persistent, check server status |
| 501 `SCREENSHOT_NOT_SUPPORTED` | Screenshot unavailable in this mode | Use connectUrl player instead |
| `DELETE_REQUIRES_TTY` | Delete without interactive terminal | Run `delete_helper.py` manually |

See `references/error_codes.md` and `scripts/error_codes.py` for the full catalog.
