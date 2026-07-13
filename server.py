"""
Vancam MCP Server — camera discovery + images.

Spatial search uses the same API as the VanCam web app (vancam.ai):
  bounds, radius, route, and nearest queries against 1M+ live cameras worldwide.

See camera_api.py and openapi.yaml for the full API specification.
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image
import sys
from typing import Any, Dict

from camera_api import (
    fetch_cameras,
    fetch_image_bytes,
    image_urls,
    MAX_LIMIT,
)

mcp = FastMCP("vancam-mcp")

_CAMERA_FIELDS_DOC = (
    "Each camera includes asset_id, latitude, longitude, street_address, direction, "
    "camera_class (open|premium), level1/level2/level3 (country/state/city), "
    "distance_meters (radius/nearest), route_fraction (route search, 0–1 along path), "
    "image_url (primary live frame), and image_urls.vancam_api. "
    "These URLs require an x-api-key header and return 403 Forbidden if opened "
    "directly (browser, bare curl, or handed to the user as a link) — call "
    "get_camera_image(asset_id) to actually fetch/display a frame."
)


def _filter_open_cameras(data: Any, active_only: bool) -> Any:
    if not active_only or not isinstance(data, dict):
        return data
    cameras = data.get("cameras")
    if not isinstance(cameras, list):
        return data
    filtered = [
        c for c in cameras
        if isinstance(c, dict) and c.get("camera_class", "open") == "open"
    ]
    out = dict(data)
    out["cameras"] = filtered
    out["count"] = len(filtered)
    return out


# ---------------------------
# Tool: List Cameras (Bounds Search)
# ---------------------------
@mcp.tool()
def list_cameras(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    limit: int = 100,
    active_only: bool = False,
) -> Dict[str, Any]:
    """
    List traffic cameras within a map bounding box.

    Same query the VanCam web app (vancam.ai) runs when the user pans/zooms
    the map. Use when the user asks for cameras in a visible map area or
    geographic rectangle.

    Parameters:
        min_lat, min_lon, max_lat, max_lon: Bounding box (WGS84)
        limit: Max cameras to return (1–100, default 100)
        active_only: If true, return only camera_class=open (live feeds)

    Returns:
        Bounds search JSON with enriched image_url per camera.
    """
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    data = fetch_cameras({
        "min_lat": min_lat,
        "min_lon": min_lon,
        "max_lat": max_lat,
        "max_lon": max_lon,
        "limit": limit,
    })
    return _filter_open_cameras(data, active_only)


# ---------------------------
# Tool: Get Cameras by Radius
# ---------------------------
@mcp.tool()
def get_cameras_by_radius(
    lat: float,
    lon: float,
    radius: float = 1.0,
    limit: int = 50,
    active_only: bool = False,
) -> Dict[str, Any]:
    """
    Get traffic cameras within a radius (km) of a lat/lon point.

    Radius search. Use when the user asks for cameras near a place,
    within X km of coordinates, or around an address they geocoded.

    Parameters:
        lat, lon: Center point (WGS84)
        radius: Search radius in kilometers (default 1.0, max 50 per API)
        limit: Max cameras (1–100, default 50)
        active_only: If true, only camera_class=open

    Returns:
        JSON with type radius_search, count, radius_km, cameras[].
    """
    if radius <= 0:
        raise ValueError("radius must be greater than 0")
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    data = fetch_cameras({
        "lat": lat,
        "lon": lon,
        "radius": radius,
        "limit": limit,
    })
    return _filter_open_cameras(data, active_only)


# ---------------------------
# Tool: Get Cameras Along Route
# ---------------------------
@mcp.tool()
def get_cameras_along_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    buffer: float = 100.0,
    limit: int = 50,
    active_only: bool = False,
) -> Dict[str, Any]:
    """
    Get traffic cameras along a straight-line route between two points.

    Same API call as the VanCam web app (vancam.ai) route view.
    Cameras are returned sorted by route_fraction (0 = origin, 1 = destination).

    Note: Uses a straight line between origin and destination (PostGIS ST_MakeLine),
    not a driving route polyline. Buffer is meters perpendicular to that line.

    Parameters:
        origin_lat, origin_lon: Route start (WGS84)
        dest_lat, dest_lon: Route end (WGS84)
        buffer: Corridor width in meters (default 100, web app uses 100)
        limit: Max cameras (1–100, default 50, web app uses 50)
        active_only: If true, only camera_class=open

    Returns:
        JSON with type route_search, buffer_meters, cameras[] with route_fraction.
    """
    if buffer <= 0:
        raise ValueError("buffer must be greater than 0")
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    data = fetch_cameras({
        "origin_lat": origin_lat,
        "origin_lon": origin_lon,
        "dest_lat": dest_lat,
        "dest_lon": dest_lon,
        "buffer": buffer,
        "limit": limit,
    }, sort_route=True)
    return _filter_open_cameras(data, active_only)


# ---------------------------
# Tool: Get Nearest Cameras
# ---------------------------
@mcp.tool()
def get_nearest_cameras(
    lat: float,
    lon: float,
    limit: int = 5,
    active_only: bool = False,
) -> Dict[str, Any]:
    """
    Get the nearest traffic cameras to a geographic point.

    Nearest-neighbor search. Use when the user asks for the closest
    camera(s) to a location.

    Parameters:
        lat, lon: Query point (WGS84)
        limit: Number of cameras (1–100, default 5)
        active_only: If true, only camera_class=open

    Returns:
        JSON with type nearest_search and cameras[] ordered by distance_meters.
    """
    if limit <= 0 or limit > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")

    data = fetch_cameras({
        "lat": lat,
        "lon": lon,
        "nearest": "true",
        "limit": limit,
    })
    return _filter_open_cameras(data, active_only)


# ---------------------------
# Tool: Get Camera Image
# ---------------------------
@mcp.tool(structured_output=False)
def get_camera_image(asset_id: str) -> Any:
    """
    Get the live frame for a camera by asset_id, embedded directly in the
    tool result.

    api.vancam.ai requires an x-api-key header this server holds — an MCP
    client fetching the bare URL itself (e.g. Claude Desktop opening the
    link) has no way to attach that header and gets 403 Forbidden. This tool
    fetches the frame server-side instead and returns the image bytes.

    Parameters:
        asset_id: Vancam camera asset ID (integer as string)

    Returns:
        The live image, plus asset_id/url metadata for reference.
    """
    if not asset_id or not str(asset_id).strip():
        raise ValueError("asset_id is required")

    aid = str(asset_id).strip()
    urls = image_urls(aid)
    image_result = fetch_image_bytes(aid)
    image_format = image_result["content_type"].split("/")[-1] or "jpeg"

    return [
        {
            "asset_id": aid,
            "url": urls["vancam_api"],
            "image_url": urls["vancam_api"],
            "image_urls": urls,
            "content_type": image_result["content_type"],
        },
        Image(data=image_result["data"], format=image_format),
    ]


# ---------------------------
# Tool: Describe camera API
# ---------------------------
@mcp.tool()
def describe_camera_api() -> Dict[str, Any]:
    """
    Describe the spatial camera API exposed by this MCP server.

    Call this first when unsure which search tool to use. Documents the same
    capabilities as the VanCam map web app (bounds pan, radius, route, nearest).
    """
    return {
        "description": "Vancam traffic camera spatial search (1M+ live open cameras worldwide)",
        "web_app_reference": "https://vancam.ai",
        "openapi_reference": "openapi.yaml",
        "search_modes": {
            "bounds": {
                "tool": "list_cameras",
                "params": ["min_lat", "min_lon", "max_lat", "max_lon", "limit"],
                "web_app_usage": "Map pan/zoom, once zoomed in past a threshold",
            },
            "radius": {
                "tool": "get_cameras_by_radius",
                "params": ["lat", "lon", "radius_km", "limit"],
            },
            "route": {
                "tool": "get_cameras_along_route",
                "params": ["origin_lat", "origin_lon", "dest_lat", "dest_lon", "buffer_m", "limit"],
                "web_app_usage": "Route view (default buffer=100, limit=50)",
                "note": "Straight-line corridor, not driving-route geometry",
            },
            "nearest": {
                "tool": "get_nearest_cameras",
                "params": ["lat", "lon", "limit"],
            },
        },
        "camera_fields": _CAMERA_FIELDS_DOC,
        "image_endpoints": {
            "vancam_api": "https://api.vancam.ai/api?asset_id={asset_id}",
        },
        "limits": {"max_results_per_query": MAX_LIMIT},
    }


if __name__ == "__main__":
    try:
        print("Vancam MCP server running on stdio", file=sys.stderr)
        print("Vancam camera discovery: bounds, radius, route, nearest", file=sys.stderr)
        mcp.run()
    except KeyboardInterrupt:
        print("Server interrupted", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error in main(): {e}", file=sys.stderr)
        sys.exit(1)
