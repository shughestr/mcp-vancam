"""
OpenLens / Vancam camera API client.

Matches the production VanCam web app (vancam_feature_along_route/upload2s3/index.html):
  - Camera search: api.vancam.ai/cameras/cameras?...
  - Live images:   api.vancam.ai/api?asset_id=...

Also supports vancam.ai/sse/* endpoints (same PostGIS backend, alternate gateway).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

# Web app sets API_ENDPOINT = 'https://api.vancam.ai/cameras' then fetches
# `${API_ENDPOINT}/cameras?${params}` → /cameras/cameras
DEFAULT_CAMERAS_SEARCH_URL = os.getenv(
    "VANCAM_CAMERAS_SEARCH_URL",
    "https://api.vancam.ai/cameras/cameras",
)
DEFAULT_VANCAM_API_IMAGE_URL = os.getenv(
    "VANCAM_API_IMAGE_URL",
    "https://api.vancam.ai/api",
)
DEFAULT_VANCAM_CAMERAS_URL = os.getenv(
    "VANCAM_SSE_CAMERAS_URL",
    "https://vancam.ai/sse/cameras",
)
DEFAULT_VANCAM_IMAGE_URL = os.getenv(
    "VANCAM_SSE_IMAGE_URL",
    "https://vancam.ai/sse/image",
)

DEFAULT_TIMEOUT_SECONDS = 15
MAX_LIMIT = 100

# api.vancam.ai requires an x-api-key header. Set VANCAM_API_KEY in your
# environment (see .env / ENV_SETUP.md) for a personal free-tier key (higher
# limits) from the web app's /account page. Falls back to a shared, low-limit
# key (1 req/s, 500/month) — meant to be public — if unset.
ANONYMOUS_SHARED_API_KEY = "abwSAo91eI8wENsNrZFUE7tC6qGkh9Tw66x4cfcQ"
VANCAM_API_KEY = os.getenv("VANCAM_API_KEY", ANONYMOUS_SHARED_API_KEY)


def _api_key_headers() -> Dict[str, str]:
    return {"x-api-key": VANCAM_API_KEY} if VANCAM_API_KEY else {}


def cameras_search_url() -> str:
    return DEFAULT_CAMERAS_SEARCH_URL


def image_urls(asset_id: Any) -> Dict[str, str]:
    aid = str(int(asset_id)) if isinstance(asset_id, float) and asset_id == int(asset_id) else str(asset_id)
    return {
        "vancam_api": f"{DEFAULT_VANCAM_API_IMAGE_URL}?asset_id={aid}",
        "vancam": f"{DEFAULT_VANCAM_IMAGE_URL}?asset_id={aid}",
    }


def normalize_asset_id(asset_id: Any) -> str:
    if asset_id is None:
        return ""
    if isinstance(asset_id, float) and asset_id == int(asset_id):
        return str(int(asset_id))
    return str(asset_id)


def enrich_camera(camera: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(camera, dict):
        return camera

    out = dict(camera)
    asset_id = out.get("asset_id")
    if asset_id is not None:
        urls = image_urls(asset_id)
        out["image_url"] = urls["vancam_api"]
        out["image_urls"] = urls

    if isinstance(out.get("asset_id"), float) and out["asset_id"] == int(out["asset_id"]):
        out["asset_id"] = int(out["asset_id"])
    elif out.get("asset_id") is not None:
        out["asset_id"] = normalize_asset_id(out["asset_id"])

    return out


def enrich_response(data: Any, *, sort_route: bool = False) -> Any:
    if not isinstance(data, dict):
        return data

    out = dict(data)
    cameras = out.get("cameras")
    if isinstance(cameras, list):
        enriched: List[Dict[str, Any]] = [enrich_camera(c) for c in cameras]
        if sort_route or out.get("type") == "route_search":
            enriched.sort(key=lambda c: (c.get("route_fraction") is None, c.get("route_fraction") or 0))
        out["cameras"] = enriched

    out["_meta"] = {
        "cameras_search_url": cameras_search_url(),
        "image_url_primary": DEFAULT_VANCAM_API_IMAGE_URL,
        "image_url_alternate": DEFAULT_VANCAM_IMAGE_URL,
        "source": "openlens",
        "image_url_warning": (
            "image_url / image_urls require an x-api-key header and return "
            "403 Forbidden if opened directly (browser, bare curl, or pasted "
            "as a link). Call the get_camera_image tool with the asset_id "
            "to fetch the actual frame."
        ),
    }
    return out


def fetch_cameras(
    params: Dict[str, Any],
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    sort_route: bool = False,
) -> Any:
    """
    Query the OpenLens spatial camera API.

    Search modes (same endpoint, different query params — see OpenAPI spec):
      - Bounds:  min_lat, min_lon, max_lat, max_lon [, limit]
      - Radius:  lat, lon, radius [, limit]
      - Route:   origin_lat, origin_lon, dest_lat, dest_lon, buffer [, limit]
      - Nearest: lat, lon, nearest=true [, limit]
    """
    clean = {k: v for k, v in params.items() if v is not None}
    if "limit" in clean:
        clean["limit"] = max(1, min(int(clean["limit"]), MAX_LIMIT))

    try:
        response = requests.get(
            cameras_search_url(), params=clean, headers=_api_key_headers(), timeout=timeout
        )
        response.raise_for_status()
        return enrich_response(response.json(), sort_route=sort_route)
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        raise RuntimeError(f"Camera API HTTP error: {status}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Camera API request failed: {e}") from e


def fetch_image_bytes(asset_id: Any, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Fetch the actual live frame bytes for asset_id from api.vancam.ai.

    The vancam_api image endpoint requires the x-api-key header this module
    holds — a plain URL handed to an MCP client (which has no way to attach
    that header) gets a 403 Forbidden from API Gateway. Fetching server-side
    here and returning the bytes avoids that.
    """
    url = image_urls(asset_id)["vancam_api"]
    try:
        response = requests.get(url, headers=_api_key_headers(), timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        return {"data": response.content, "content_type": content_type}
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        raise RuntimeError(f"Camera image HTTP error: {status}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Camera image request failed: {e}") from e


def fetch_cameras_vancam_sse(params: Dict[str, Any], **kwargs: Any) -> Any:
    """Same queries via vancam.ai/sse/cameras (alternate gateway)."""
    clean = {k: v for k, v in params.items() if v is not None}
    if "limit" in clean:
        clean["limit"] = max(1, min(int(clean["limit"]), MAX_LIMIT))

    try:
        response = requests.get(DEFAULT_VANCAM_CAMERAS_URL, params=clean, timeout=kwargs.get("timeout", DEFAULT_TIMEOUT_SECONDS))
        response.raise_for_status()
        data = enrich_response(response.json(), sort_route=kwargs.get("sort_route", False))
        if isinstance(data, dict) and isinstance(data.get("_meta"), dict):
            data["_meta"]["cameras_search_url"] = DEFAULT_VANCAM_CAMERAS_URL
        return data
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "unknown"
        raise RuntimeError(f"Vancam SSE API HTTP error: {status}") from e
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Vancam SSE API request failed: {e}") from e
