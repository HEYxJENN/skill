# Screen Control — WebRTC connectUrl Workflow

Farmce uses a **WebRTC player** for Android screen control, not ADB or uiautomator2.
When a session is running, you get a `connectUrl` — open it in a browser to see and interact with the Android screen.

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

Since there is no direct DOM access, the recommended approach for AI agents is:

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
- Type text into focused fields
- Press Back/Home buttons in the toolbar

### 4. Verify action succeeded
Take another screenshot and confirm the expected screen state.

### 5. Retry on failure
If the expected state is not reached after 3 attempts (e.g. element not found), log the screenshot and report the blocker.

---

## Session lifecycle notes

- Sessions are **shared-state**: after stopping, the Android state (apps, login sessions, files) is preserved for the next run.
- Sessions auto-stop after ~45 minutes of server-side inactivity.
- Always call `client.stop_session(profile_id)` when your automation task is done to preserve quota.

---

## Proxy and geolocation

For geo-specific content (TikTok regional feed, Instagram location, etc.), attach a proxy before starting the session:

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

---

## Comparison with ADB-based approaches

| Feature | Farmce (connectUrl) | ADB / uiautomator2 |
|---------|--------------------|--------------------|
| Connection | HTTPS / WebRTC | ADB over TCP |
| Screen view | Browser / video stream | Screenshots + XML hierarchy |
| Element targeting | Visual (click position) | resourceId, text, xpath |
| Input | Browser events → WebRTC | ADB input commands |
| Dependencies | None (browser-use) | adb, uiautomator2, glogin |
| State persistence | Server-side (profile) | Device filesystem |

For visual automation the approach is: **screenshot → vision model → click coordinates**.
