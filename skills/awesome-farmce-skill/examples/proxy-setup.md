# Example: Proxy Setup

Proxies route all Android network traffic through a specific IP. Attach a proxy to a profile to control the device's apparent geolocation and IP address.

---

## Add and attach a proxy

```python
from scripts.farmce_client import FarmceClient

client = FarmceClient()

# 1. Check proxy connectivity first
check = client.check_proxy(
    host="proxy.example.com",
    port=8080,
    login="user",
    password="pass",
    protocol="http",
)
if check["status"] != "ok":
    raise SystemExit("Proxy check failed — verify credentials and host")

print("Proxy is reachable.")

# 2. Save proxy to your account
proxy_resp = client.add_proxy(
    host="proxy.example.com",
    port="8080",
    login="user",
    password="pass",
    protocol="http",
    connection_type="residential",  # or "mobile", "datacenter"
    country_code="US",
)
proxy_id = proxy_resp["data"]["id"]
print(f"Proxy saved: {proxy_id}")

# 3. Attach to profile
profile_id = "your_profile_id"
client.update_profile(profile_id, proxy={"id": proxy_id})
print(f"Proxy attached to profile {profile_id}")

# 4. Start session — proxy is applied automatically
from scripts.session_helper import run_session
session = run_session(profile_id, client=client)
print(f"Session with US proxy running: {session['connectUrl']}")
```

---

## Use Farmce-managed proxy

Farmce can provision a proxy automatically (no external provider needed):

```python
proxy_resp = client.add_proxy(
    host="",    # not needed for farmce mode
    port="",
    # Set mode via direct API call
)

# Or via direct call:
proxy_resp = client.post(
    "/api/workspace/proxies",
    body={
        "mode": "farmce",
        "countryCode": "US",
    },
)
proxy_id = proxy_resp["data"]["id"]
```

---

## List saved proxies

```python
proxies = client.list_proxies()
for p in proxies:
    print(f"{p['id']} — {p.get('host', 'farmce-managed')} ({p.get('countryCode', '?')})")
```

---

## Remove proxy from profile

```python
# Set proxy to null to remove it
client.update_profile(profile_id, proxy=None)
```

---

## Notes

- The proxy is applied at the Android OS level — all apps on the device route through it.
- Proxy change takes effect on the **next session start**, not the current one.
- For geo-targeted automation (TikTok region, Instagram location), always set the proxy and matching `countryCode` on the profile before starting.
- `residential` proxies have better platform trust scores than `datacenter` for social media automation.
