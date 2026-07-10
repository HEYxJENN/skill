# Example: Start a Session and Control the Screen

This example shows the full workflow from checking limits to opening a session and taking a screenshot.

---

## Prerequisites

```bash
python scripts/init_config.py   # one-time setup
python scripts/doctor.py        # verify everything works
```

---

## Full Python example

```python
from scripts.farmce_client import FarmceClient
from scripts.session_helper import run_session, stop_session
from scripts.screenshot import take_screenshot

client = FarmceClient()

# 1. Check quota before starting
usage = client.get_usage()
data = usage.get("data")
if not data:
    raise SystemExit("No active tariff. Subscribe at https://app.farmce.com")
if data.get("minutesRemaining", 1) <= 0:
    raise SystemExit("Quota exhausted. Upgrade your plan.")

# 2. Pick a profile
profiles = client.list_profiles().get("profiles", [])
if not profiles:
    raise SystemExit("No profiles found. Create one at https://app.farmce.com")

profile = profiles[0]
profile_id = profile["id"]
print(f"Using profile: {profile['name']} ({profile_id})")

# 3. Start session
session = run_session(profile_id, client=client)
if not session:
    raise SystemExit("Failed to start session. Check doctor.py output.")

connect_url = session["connectUrl"]
print(f"\nSession ready!")
print(f"connectUrl: {connect_url}")
print(f"\nOpen the connectUrl in a browser to control the Android screen.")

# 4. Take a screenshot to see the current screen
try:
    result = take_screenshot(profile_id, client=client, save_to="/tmp/farmce_screen.png")
    if result and result.get("imageBase64"):
        print("Screenshot saved to /tmp/farmce_screen.png")
except Exception as e:
    print(f"Screenshot not available ({e}), use connectUrl to view the screen")

# 5. ... do your automation work here ...

# 6. Stop when done
stop_session(profile_id, client=client)
print("Session stopped.")
```

---

## CLI equivalent

```bash
# Start session
python scripts/session_helper.py --profile-id <profile_id>

# Get status of running session
python scripts/session_helper.py --profile-id <profile_id> --status

# Screenshot
python scripts/screenshot.py --profile-id <profile_id> --output /tmp/screen.png

# Stop session
python scripts/session_helper.py --profile-id <profile_id> --stop
```

---

## Agent prompts

Tell your AI agent:

```
"List my Farmce profiles, start a session on the first one, and give me the connectUrl"

"Check my Farmce quota, then start profile TikTok-US and take a screenshot"

"Stop all running Farmce sessions"
```

---

## Notes

- `run_session()` polls until the session is `running` (up to 120 seconds by default).
- If the session does not start in time, check `doctor.py` — the issue is usually quota or plan limits.
- The `connectUrl` is stable for the duration of the session; you can reopen it without calling `run` again.
- After `stop`, the session is gone but the profile state is preserved.
