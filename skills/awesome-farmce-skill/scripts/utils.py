#!/usr/bin/env python3
"""Shared utilities: config loading and HTTP helpers."""

import json
import os
import uuid

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "assets",
    "config.json",
)


def load_config() -> dict:
    path = os.path.abspath(_CONFIG_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Config not found at {path}. Run: python scripts/init_config.py"
        )
    with open(path) as f:
        cfg = json.load(f)
    if not cfg.get("bearer_token") or cfg["bearer_token"] == "YOUR_BEARER_TOKEN_HERE":
        raise ValueError(
            "bearer_token is not set. Run: python scripts/init_config.py"
        )
    return cfg


def save_config(cfg: dict) -> None:
    path = os.path.abspath(_CONFIG_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def get_bearer_token() -> str:
    return load_config()["bearer_token"]


def get_base_url() -> str:
    return load_config().get("base_url", "https://app.farmce.com").rstrip("/")


def generate_request_id() -> str:
    return str(uuid.uuid4())
