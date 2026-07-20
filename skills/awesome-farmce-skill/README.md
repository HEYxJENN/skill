# Farmce Cloud Android Skill

> 🤖 Farmce cloud Android API automation for AI agents

[![Status](https://img.shields.io/badge/Status-Beta-orange.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

---

> ⚠️ **WARNING: BETA**
>
> This skill drives real Farmce cloud devices via an AI agent. It is **beta** — use carefully, prefer the flows in `examples/`, and confirm costly or destructive steps.
>
> - Sessions bill subscription minutes; **always stop** when finished.
> - API and session behavior may change; expect occasional manual fixes.
> - Control path is **REST + WebRTC `connectUrl` + screenshots** only (no local ADB / device shell).

---

## Overview

Farmce Skill provides automation for the [Farmce](https://app.farmce.com) cloud Android service, enabling AI agents to manage persistent Android profiles, start WebRTC sessions, take screenshots, configure proxies, and interact with Android apps via the API.

Farmce exposes a **REST API + WebRTC player** (not local ADB). Screen control uses the `connectUrl` from a started session — open it in a browser-use tool or any WebRTC client. Do not assume `adb`, device serials, or on-device UI automation libraries.

---

## Features

- **Profile management** — create, list, and configure saved Android states
- **Session control** — start / stop cloud Android sessions with auto-polling
- **Screen access** — `connectUrl` WebRTC player for tap, swipe, type, Back/Home
- **Screenshots** — REST endpoint for capturing the current screen
- **Proxy support** — add, verify, and attach proxies to profiles
- **Diagnostics** — `doctor.py` validates auth, limits, and API reachability

---

## Requirements

```bash
# Python 3.9+
pip install -r requirements.txt
```

No local ADB or on-device UI automation packages required.

---

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Initialize credentials

```bash
python scripts/init_config.py
```

This sends a magic link to your Farmce email and saves your Bearer token to `assets/config.json`.

### 3. Verify everything works

```bash
python scripts/doctor.py
```

### 4. Start a session

```bash
python scripts/session_helper.py --profile-id <your_profile_id>
```

Or tell your AI agent:

```
"List my Farmce profiles and start a session on the first one"
"Take a screenshot of profile TikTok-US"
"Stop all active sessions"
```

---

## Prompt Examples

Once configured, tell your AI agent what to do:

### List phones / profiles

```
"Show me all my Farmce profiles and their status"
"List my cloud Android devices"
```

### Start a session

```
"Start profile TikTok-US and give me the connectUrl"
"Boot my Android profile named Instagram-1"
```

### Screenshot

```
"Take a screenshot of my running Android session (profile: abc123)"
```

### Proxy

```
"Add a US residential proxy to profile TikTok-US"
"Check if proxy proxy.example.com:8080 is working"
```

### Stop

```
"Stop the active session on profile TikTok-US"
"Stop all running sessions"
```

The agent should:
- Do **only** what you asked — no extra create/start/delete
- Ask if the profile ID or action is ambiguous
- Check limits before starting
- Poll session status until ready and return `connectUrl`
- Classify errors (quota, auth, plan limit)
- Stop sessions it started when the task is done

---

## Important Notes

1. **Beta:** Treat this as experimental. Prefer scenarios from `examples/` over free-form automation.
2. **API only:** No local ADB or on-device shell. Control is REST + WebRTC `connectUrl` + screenshots.
3. **Credentials:** Loaded from `assets/config.json`. Do not paste Bearer tokens into chat.
4. **Deletion:** Use `scripts/delete_helper.py` with interactive `YES` — agents must not bypass confirmation.
5. **Cost:** Running sessions bill minutes. Always stop when finished.

---

## File Structure

```
awesome-farmce-skill/
├── SKILL.md                   # Agent usage guide (read this first)
├── README.md                  # This file
├── LICENSE
├── requirements.txt
├── assets/
│   └── config.json            # base_url + bearer_token (.gitignore)
├── scripts/
│   ├── __init__.py
│   ├── utils.py               # Config loader, helpers
│   ├── farmce_client.py       # REST client (Bearer auth, endpoint whitelist)
│   ├── init_config.py         # Magic link → save Bearer token
│   ├── doctor.py              # Diagnose auth, limits, API reachability
│   ├── session_helper.py      # run / poll status / stop → connectUrl
│   ├── screenshot.py          # Capture screenshot via REST
│   ├── error_codes.py         # Structured error codes for agents
│   └── delete_helper.py       # Interactive profile delete (YES confirm)
├── references/
│   ├── screen_control.md      # WebRTC connectUrl workflow
│   ├── error_codes.md         # All error codes and remediation
│   ├── best_practices.md      # Cost-saving and reliability tips
│   └── profiles_and_devices.md  # Entities and lifecycle
└── examples/
    ├── start-session.md
    └── proxy-setup.md
```

---

## Links

- [Farmce App](https://app.farmce.com)
- [Live OpenAPI spec](https://app.farmce.com/api/openapi.json)
- [Interactive API docs (Scalar)](https://app.farmce.com/api/swagger)

---

## License

Apache License 2.0
