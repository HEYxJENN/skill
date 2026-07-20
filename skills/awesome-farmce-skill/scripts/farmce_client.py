#!/usr/bin/env python3
"""Farmce REST API client with Bearer auth and endpoint whitelist.

Mandatory rules enforced in code:
1. Only allowed endpoints can be called — guessing is blocked.
2. Credentials are read from assets/config.json, never passed via arguments.
"""

import sys
import os
import requests

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scripts.utils import get_bearer_token, get_base_url

ALLOWED_ENDPOINTS = {
    # Auth
    "POST /api/auth/token/magic-link",
    # User
    "GET /api/users/me",
    "GET /api/users/me/usage",
    # Billing
    "GET /api/payments/tariffs",
    "GET /api/payments/history",
    # Devices
    "GET /api/phones/allocations",
    "POST /api/phones/allocations/{id}/attach",
    # Profiles
    "GET /api/workspace/profiles",
    "POST /api/workspace/profiles",
    "PATCH /api/workspace/profiles/{id}",
    "DELETE /api/workspace/profiles/{id}",
    # Sessions
    "POST /api/workspace/profiles/{id}/run",
    "GET /api/workspace/profiles/{id}/status",
    "POST /api/workspace/profiles/{id}/stop",
    "POST /api/workspace/profiles/{id}/screenshot",
    # Proxy
    "GET /api/workspace/proxies",
    "POST /api/workspace/proxies",
    "POST /api/proxy/check",
}


class FarmceForbiddenError(Exception):
    pass


class FarmceClient:
    def __init__(self, token: str = None, base_url: str = None):
        self.token = token or get_bearer_token()
        self.base_url = (base_url or get_base_url()).rstrip("/")

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

    def _check_endpoint(self, method: str, path_template: str) -> None:
        key = f"{method.upper()} {path_template}"
        if key not in ALLOWED_ENDPOINTS:
            raise FarmceForbiddenError(
                f"Endpoint '{key}' is not in the whitelist. "
                "Consult SKILL.md or https://app.farmce.com/api/swagger for the full list."
            )

    def get(self, path: str, path_template: str = None, params: dict = None, timeout: int = 20) -> dict:
        self._check_endpoint("GET", path_template or path)
        resp = requests.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=params,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, path_template: str = None, body: dict = None, timeout: int = 20) -> dict:
        self._check_endpoint("POST", path_template or path)
        resp = requests.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            json=body or {},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def patch(self, path: str, path_template: str = None, body: dict = None, timeout: int = 20) -> dict:
        self._check_endpoint("PATCH", path_template or path)
        resp = requests.patch(
            f"{self.base_url}{path}",
            headers=self._headers(),
            json=body or {},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def delete(self, path: str, path_template: str = None, timeout: int = 20) -> dict:
        self._check_endpoint("DELETE", path_template or path)
        resp = requests.delete(
            f"{self.base_url}{path}",
            headers=self._headers(),
            timeout=timeout,
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {"ok": True}

    # ── Convenience methods ───────────────────────────────────────────────────

    def get_me(self) -> dict:
        return self.get("/api/users/me")

    def get_usage(self) -> dict:
        return self.get("/api/users/me/usage")

    def get_tariffs(self) -> dict:
        return self.get("/api/payments/tariffs")

    def get_payment_history(self) -> dict:
        return self.get("/api/payments/history")

    def list_devices(self, status: str = None) -> dict:
        params = {"status": status} if status else None
        return self.get("/api/phones/allocations", params=params)

    def attach_device(self, allocation_id: str, profile_id: str) -> dict:
        return self.post(
            f"/api/phones/allocations/{allocation_id}/attach",
            path_template="/api/phones/allocations/{id}/attach",
            body={"profileId": profile_id},
        )

    def list_profiles(self) -> dict:
        return self.get("/api/workspace/profiles")

    def create_profile(self, name: str, country_code: str = None, proxy: dict = None) -> dict:
        body = {"name": name}
        if country_code:
            body["countryCode"] = country_code
        if proxy:
            body["proxy"] = proxy
        return self.post("/api/workspace/profiles", body=body)

    def update_profile(self, profile_id: str, name: str = None, country_code: str = None,
                       proxy: dict = None) -> dict:
        body = {}
        if name is not None:
            body["name"] = name
        if country_code is not None:
            body["countryCode"] = country_code
        if proxy is not None:
            body["proxy"] = proxy
        return self.patch(
            f"/api/workspace/profiles/{profile_id}",
            path_template="/api/workspace/profiles/{id}",
            body=body,
        )

    def delete_profile(self, profile_id: str, *, confirmed: bool = False) -> dict:
        """Delete a profile. Agents MUST use scripts/delete_helper.py instead.

        Pass confirmed=True only after interactive YES confirmation.
        """
        if not confirmed:
            raise FarmceForbiddenError(
                "Profile delete blocked without confirmation. "
                "Run: python scripts/delete_helper.py"
            )
        return self.delete(
            f"/api/workspace/profiles/{profile_id}",
            path_template="/api/workspace/profiles/{id}",
        )

    def run_session(self, profile_id: str) -> dict:
        return self.post(
            f"/api/workspace/profiles/{profile_id}/run",
            path_template="/api/workspace/profiles/{id}/run",
        )

    def get_status(self, profile_id: str) -> dict:
        return self.get(
            f"/api/workspace/profiles/{profile_id}/status",
            path_template="/api/workspace/profiles/{id}/status",
        )

    def stop_session(self, profile_id: str) -> dict:
        return self.post(
            f"/api/workspace/profiles/{profile_id}/stop",
            path_template="/api/workspace/profiles/{id}/stop",
        )

    def take_screenshot(self, profile_id: str) -> dict:
        return self.post(
            f"/api/workspace/profiles/{profile_id}/screenshot",
            path_template="/api/workspace/profiles/{id}/screenshot",
        )

    def list_proxies(self) -> dict:
        return self.get("/api/workspace/proxies")

    def add_proxy(self, host: str, port: str, login: str = None, password: str = None,
                  protocol: str = "http", connection_type: str = None,
                  country_code: str = None) -> dict:
        body = {"host": host, "port": port, "protocol": protocol}
        if login:
            body["login"] = login
        if password:
            body["password"] = password
        if connection_type:
            body["connectionType"] = connection_type
        if country_code:
            body["countryCode"] = country_code
        return self.post("/api/workspace/proxies", body=body)

    def check_proxy(self, host: str, port: int, login: str = None,
                    password: str = None, protocol: str = "http") -> dict:
        body = {"host": host, "port": port, "protocol": protocol}
        if login:
            body["login"] = login
        if password:
            body["password"] = password
        return self.post("/api/proxy/check", body=body)
