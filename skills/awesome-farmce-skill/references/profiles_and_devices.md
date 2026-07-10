# Profiles and Devices

## Entity model

```
User
 └── Allocation (rented cloud phone)
      └── Profile (saved Android state, can be attached to an allocation)
           └── Session (active run: connectUrl, sessionId, instanceId)
                └── Proxy (network route for the session)
```

---

## Allocation (cloud phone)

A rented physical cloud Android device from Farmce's pool.

**Get allocations:**

```python
resp = client.list_devices()
for alloc in resp["allocations"]:
    print(alloc["id"], alloc["status"])  # status: "active" | "expired" | ...
```

**Attach to profile** (required before starting a session for the first time):

```python
client.attach_device(allocation_id="alloc_abc", profile_id="prof_xyz")
```

You typically attach once; the binding persists until detached.

---

## Profile (Android state)

A profile is a persistent Android environment: installed apps, account logins, files, settings, and proxy config. It is the main entity you work with for automation.

**Create a profile:**

```python
profile = client.create_profile("TikTok US", country_code="US")
profile_id = profile["data"]["id"]
```

**List profiles:**

```python
resp = client.list_profiles()
profiles = resp["profiles"]          # list of profile objects
limits   = resp["limits"]            # { maxProfiles, activeRentedPhones }
```

Profile fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Profile ID used in all session endpoints |
| `name` | string | Display name |
| `status` | string | `idle` or `running` |
| `countryCode` | string | Associated country |
| `proxy` | object | Attached proxy config |
| `createdAt` | string | ISO timestamp |

**Update a profile** (name, country, proxy):

```python
client.update_profile(profile_id, proxy={
    "host": "proxy.example.com",
    "port": "8080",
    "login": "user",
    "password": "pass",
    "protocol": "http",
})
```

---

## Session (active run)

A session represents an active Android instance for a profile. It is created by `POST .../run` and destroyed by `POST .../stop` (or by server TTL).

Session flow:

```
POST /api/workspace/profiles/{id}/run
  → 200 { status: "starting" | "running", url?, session_id?, instance_id? }

GET /api/workspace/profiles/{id}/status     (poll until status = "running")
  → 200 { profileId, status, android: { sessionId, instanceId }, url }

POST /api/workspace/profiles/{id}/stop
  → 200 { ok: true }
```

Once `status = "running"` and `url` is set, open `url` (the `connectUrl`) in a browser to control the device.

---

## Proxy

Proxies are stored per-user and attached to profiles.

**Add proxy:**

```python
proxy = client.add_proxy(
    host="proxy.example.com",
    port="8080",
    login="user",
    password="pass",
    protocol="http",               # "http" | "socks5"
    connection_type="residential", # "residential" | "mobile" | "datacenter"
    country_code="US",
)
```

**Check connectivity before attaching:**

```python
result = client.check_proxy("proxy.example.com", 8080, "user", "pass")
if result["status"] == "ok":
    client.update_profile(profile_id, proxy={"id": proxy["data"]["id"]})
```

**List saved proxies:**

```python
proxies = client.list_proxies()
```

---

## Plan limits

Plan limits affect how many profiles and concurrent sessions you can have:

| Limit | Check via |
|-------|-----------|
| Max profiles | `GET /api/workspace/profiles` → `limits.maxProfiles` |
| Max concurrent sessions | `GET /api/users/me/usage` → `maxConcurrentSessions` |
| Minutes remaining | `GET /api/users/me/usage` → `minutesRemaining` |
| Rented phones | `GET /api/workspace/profiles` → `limits.activeRentedPhones` |

```python
me = client.get_me()
usage = client.get_usage()
```
