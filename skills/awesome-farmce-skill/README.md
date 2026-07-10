# Farmce Cloud Android Skill

> 🤖 Farmce cloud Android API automation for AI agents

[![Status](https://img.shields.io/badge/Status-MVP-blue.svg)]()

---

> ⚠️ **Note:** This skill controls real cloud Android devices that consume time from your Farmce subscription. Sessions cost minutes from your plan — always stop them when done.

---

## Overview

Farmce Skill provides automation for the [Farmce](https://app.farmce.com) cloud Android service, enabling AI agents to manage persistent Android profiles, start WebRTC sessions, take screenshots, configure proxies, and interact with Android apps.

Unlike ADB-based tools, Farmce exposes a **REST API + WebRTC player**. Screen control happens through the `connectUrl` returned when a session starts — agents open this URL in a browser-use tool or any WebRTC client.

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

No ADB. No `uiautomator2`. No local Android tooling required.

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

The agent handles:
- Checking limits before starting
- Polling session status until ready
- Returning the connectUrl for screen control
- Error classification (quota, auth, plan limit)

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
│   └── screenshot.py          # Capture screenshot via REST
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
