#!/usr/bin/env python3
"""Capture a screenshot of a running Android session.

Usage (CLI):
    python scripts/screenshot.py --profile-id <id>
    python scripts/screenshot.py --profile-id <id> --output /tmp/screen.png
    python scripts/screenshot.py --profile-id <id> --json

Usage (library):
    from scripts.screenshot import take_screenshot

    result = take_screenshot("profile_id")
    # result["imageBase64"]  — PNG as base64 string, or None
    # result["imageUrl"]     — URL to image, or None
"""

import sys
import os
import json
import base64
import argparse
from typing import Optional

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from scripts.farmce_client import FarmceClient
from scripts.error_codes import classify_error


def take_screenshot(
    profile_id: str,
    client: FarmceClient = None,
    save_to: Optional[str] = None,
) -> Optional[dict]:
    """Capture a screenshot of the running session.

    Args:
        profile_id: Profile ID with an active session.
        client: FarmceClient instance (auto-created from config if None).
        save_to: Optional file path to save the PNG (requires imageBase64 in response).

    Returns:
        dict with { imageBase64, imageUrl, mimeType, takenAt } or None on error.
    """
    c = client or FarmceClient()

    print(f"📸 Capturing screenshot for profile {profile_id}…")
    try:
        resp = c.take_screenshot(profile_id)
    except Exception as e:
        classify_error(e).print()
        return None

    image_b64 = resp.get("imageBase64")
    image_url = resp.get("imageUrl")
    mime = resp.get("mimeType", "image/png")
    taken_at = resp.get("takenAt", "")

    if not image_b64 and not image_url:
        print("⚠️ Screenshot response contained no image data.")
        return resp

    print(f"✅ Screenshot captured at {taken_at or 'N/A'}")
    if image_url:
        print(f"   imageUrl: {image_url}")
    if image_b64:
        print(f"   imageBase64: {len(image_b64)} chars ({mime})")

    if save_to and image_b64:
        try:
            img_bytes = base64.b64decode(image_b64)
            with open(save_to, "wb") as f:
                f.write(img_bytes)
            print(f"   Saved to: {save_to}")
        except Exception as e:
            print(f"⚠️ Could not save image: {e}")

    return resp


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Farmce screenshot capture")
    parser.add_argument("--profile-id", required=True, help="Profile ID with active session")
    parser.add_argument("--output", help="Save PNG to this file path (requires imageBase64)")
    parser.add_argument("--json", action="store_true", help="Print full response as JSON")
    args = parser.parse_args()

    result = take_screenshot(args.profile_id, save_to=args.output)

    if args.json:
        if result and result.get("imageBase64"):
            safe = {**result, "imageBase64": f"<{len(result['imageBase64'])} chars>"}
        else:
            safe = result or {}
        print(json.dumps(safe, indent=2))

    sys.exit(0 if result else 1)
