# Best Practices

## Cost management

**Always stop sessions when done.**
Sessions consume minutes from your plan from the moment they start until stopped. The server auto-stops sessions ~10 minutes after the last player heartbeat — always call `stop` when done; don't rely on the sweeper.

```python
try:
    session = run_session(profile_id)
    # ... automation work ...
finally:
    client.stop_session(profile_id)
```

**Check quota before starting.** A denied session still takes time to fail. Check first:

```python
usage = client.get_usage()
data = usage.get("data")
if not data or data.get("minutesRemaining", 1) <= 0:
    raise RuntimeError("No quota — upgrade plan before proceeding")
```

**Run `doctor.py` before long automation runs.** It surfaces auth/quota issues before you start.

---

## Session management

**One profile = one phone identity.** Do not run the same profile on multiple sessions simultaneously — it is not supported and will result in a 409.

**State is preserved.** When you stop a session and start it again on the same profile, the Android environment (installed apps, logged-in accounts, files) is exactly as you left it. You do not need to reinstall or re-login unless the profile was explicitly reset.

**Proxy is profile-level.** Set the proxy on the profile before starting a session. Changing the proxy after the session starts has no immediate effect — it takes effect on the next session start.

---

## Reliability

**Poll status after `run`.** The `POST .../run` response may return `status: "starting"` before the instance is ready. Always poll `GET .../status` until `status == "running"` and `url` is set. `session_helper.py` does this automatically.

**Retry on 502.** Upstream cloud provider errors are transient. Retry once after 30 seconds before treating it as a hard failure.

**Verify connectUrl is working** before starting UI automation: open it in the browser tool and confirm the screen is visible.

---

## Security

**Never commit `assets/config.json`.** The `.gitignore` file already excludes it. Verify with:

```bash
git status assets/
# config.json should not appear
```

**Never paste your Bearer token in chat.** Scripts load it from `config.json` automatically. If an agent asks for a token, tell it to call `client.get_me()` instead — the token is already loaded.

**Refresh tokens when needed.** If you get 401, run `python scripts/init_config.py` — it does not delete other settings in `config.json`.

---

## Multi-profile automation

To run automation on multiple profiles in sequence:

```python
from scripts.farmce_client import FarmceClient
from scripts.session_helper import run_session, stop_session

client = FarmceClient()
profiles = client.list_profiles().get("profiles", [])

for profile in profiles:
    pid = profile["id"]
    try:
        session = run_session(pid, client=client)
        if not session:
            print(f"Skipping {pid} — could not start")
            continue
        # ... work on this profile ...
    finally:
        stop_session(pid, client=client)
```

Do not start all sessions simultaneously unless your plan's concurrent session limit allows it. Check `maxConcurrentSessions` from `GET /api/users/me/usage`.

---

## Debugging

**Start with `doctor.py`:**

```bash
python scripts/doctor.py --profile-id <your_profile_id>
```

**Check session status directly:**

```bash
python scripts/session_helper.py --profile-id <id> --status
```

**Inspect full API responses** by calling the client directly:

```python
from scripts.farmce_client import FarmceClient
import json

client = FarmceClient()
print(json.dumps(client.get_me(), indent=2))
print(json.dumps(client.get_usage(), indent=2))
```

**For persistent 502s or unexpected behavior**, check the Farmce status page or contact support.
