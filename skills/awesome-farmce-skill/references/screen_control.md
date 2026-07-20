# Screen Control — WebRTC connectUrl Workflow

Farmce controls the Android screen through a **WebRTC player** at `connectUrl`.
When a session is running, open that URL in a browser to see and interact with the device.

---

## How it works

```
POST .../run  →  poll GET .../status  →  status="running" + connectUrl ready
                                          ↓
                                Open connectUrl in browser
                                          ↓
                              Tap / Swipe / Type / Back / Home
```

The connectUrl serves an HTML5 WebRTC player (`armcloud-rtc`) that streams the Android screen and forwards input events.

---

## Getting connectUrl

```python
from scripts.session_helper import run_session

session = run_session("your_profile_id")
print(session["connectUrl"])  # → https://...
```

Or check an already-running session:

```python
from scripts.farmce_client import FarmceClient

client = FarmceClient()
status = client.get_status("your_profile_id")
# status["url"] is the connectUrl when session is running
```

---

## Screen interactions

The player supports these input methods:

| Action | How |
|--------|-----|
| **Tap** | Click on the element in the player |
| **Swipe** | Click-drag (scroll, dismiss, navigate) |
| **Type** | Focus a text field in the player, then type |
| **Back** | On-screen Back button in the player toolbar |
| **Home** | On-screen Home button in the player toolbar |
| **Recents** | On-screen Recents button |
| **Volume up/down** | Volume buttons in the player toolbar |

> For browser-use automation (e.g. Playwright, Cursor browser tool), navigate to the `connectUrl` and interact with it like a normal webpage.

---

## Agent rules for screen control (MANDATORY)

Do **only** the UI steps the user asked for. Do not “helpfully” complete setup on your own.

**Forbidden unless the user explicitly requested it:**
- Auto-login to apps (Google, social apps, stores, email, etc.)
- Entering or requesting passwords / 2FA / recovery codes
- Changing system settings (language, locale, timezone, developer options, permissions defaults)
- Installing / updating apps “because it looks needed”
- Accepting terms, cookies, or permission dialogs beyond what the task requires
- Creating accounts or linking services
- Filling forms with invented data

If a login wall, onboarding, or settings screen appears and the user did not ask to handle it — **stop and ask**. Describe what you see; wait for instructions.

Visual automation loop (when the user *did* ask for UI steps):

1. Screenshot → vision → identify target  
2. Click / type via the player  
3. Screenshot again to verify  
4. After ~3 failed attempts, report the blocker with a screenshot — do not invent a workaround

---

## Screenshot

For reading the screen state without keeping the player open, use the screenshot REST endpoint:

```python
from scripts.screenshot import take_screenshot

result = take_screenshot("your_profile_id")

# result["imageBase64"]  → PNG image as base64 string
# result["imageUrl"]     → direct URL if provided by the backend
# result["mimeType"]     → "image/png"
# result["takenAt"]      → ISO timestamp
```

Or via CLI:

```bash
# Print metadata
python scripts/screenshot.py --profile-id <id>

# Save PNG to file
python scripts/screenshot.py --profile-id <id> --output /tmp/screen.png
```

> **Note:** Screenshot returns `501 Not Supported` in certain backend configurations. In that case, use the connectUrl player directly — navigate to it with a browser tool and take a screenshot of the page.

---

## Agent workflow for UI automation

Only when the user explicitly asked for screen interaction:

### 1. Start session and open player
```python
session = run_session(profile_id)
connect_url = session["connectUrl"]
# → navigate browser tool to connect_url
```

### 2. Read screen state via screenshot
```python
result = take_screenshot(profile_id)
# Pass result["imageBase64"] to vision model to identify UI elements
```

### 3. Interact through the player
Use browser-use tool to:
- Click on the element's position in the player viewport
- Type text into focused fields **only if the user provided the text / asked to type**
- Press Back/Home buttons in the toolbar when needed for the stated task

### 4. Verify action succeeded
Take another screenshot and confirm the expected screen state.

### 5. Retry on failure
If the expected state is not reached after 3 attempts (e.g. element not found), log the screenshot and report the blocker. Do not invent logins, settings changes, or side quests.

---

## Session lifecycle notes

- Sessions are **shared-state**: after stopping, the Android state (apps, login sessions, files) is preserved for the next run.
- Sessions auto-stop ~10 minutes after the last player heartbeat (the `connectUrl` page pings every ~30s while open). Without an open player, REST-only work can still lose the session.
- Always call `client.stop_session(profile_id)` when your automation task is done to preserve quota.

---

## Proxy and geolocation

Attach a proxy **only if the user asked**. Example:

```python
client.update_profile(profile_id, proxy={
    "host": "proxy.example.com",
    "port": "8080",
    "login": "user",
    "password": "pass",
    "protocol": "http",
    "connectionType": "residential",
    "countryCode": "US",
})
```

The proxy is applied at the Android network level for the duration of the session.
