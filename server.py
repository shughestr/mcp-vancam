from mcp.server.fastmcp import FastMCP
import requests
import sys

mcp = FastMCP("vancam-mcp")

# Base API URL
BASE_URL = "https://vancam.ai"

# ---------------------------
# Tool: List Cameras (Bounds Search)
# ---------------------------
@mcp.tool()
def list_cameras(min_lat: float, min_lon: float, max_lat: float, max_lon: float):
    """List all cameras within bounding box."""
    # Validate parameters
    if min_lat is None or min_lon is None or max_lat is None or max_lon is None:
        raise ValueError("Missing required parameters: min_lat, min_lon, max_lat, max_lon")
    
    url = (
        f"{BASE_URL}/sse/cameras"
        f"?min_lat={min_lat}&min_lon={min_lon}&max_lat={max_lat}&max_lon={max_lon}"
    )
    
    try:
        res = requests.get(url)
        res.raise_for_status()  # Raise an exception for bad status codes
        return res.json()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error! status: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch cameras: {str(e)}")

# ---------------------------
# Tool: Get Cameras by Radius
# ---------------------------
@mcp.tool()
def get_cameras_by_radius(lat: float, lon: float, radius: float = 1.0):
    """Get cameras within specified radius (in km) around a geo point."""
    # Validate parameters
    if lat is None or lon is None:
        raise ValueError("Missing required parameters: lat, lon")
    if radius is None or radius <= 0:
        raise ValueError("Radius must be greater than 0")
    
    url = (
        f"{BASE_URL}/sse/cameras"
        f"?lat={lat}&lon={lon}&radius={radius}"
    )
    
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error! status: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch cameras: {str(e)}")

# ---------------------------
# Tool: Get Cameras Along Route
# ---------------------------
@mcp.tool()
def get_cameras_along_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, buffer: float = 100.0):
    """Get cameras along a route between origin and destination points."""
    # Validate parameters
    if origin_lat is None or origin_lon is None or dest_lat is None or dest_lon is None:
        raise ValueError("Missing required parameters: origin_lat, origin_lon, dest_lat, dest_lon")
    if buffer is None or buffer <= 0:
        raise ValueError("Buffer must be greater than 0")
    
    url = (
        f"{BASE_URL}/sse/cameras"
        f"?origin_lat={origin_lat}&origin_lon={origin_lon}"
        f"&dest_lat={dest_lat}&dest_lon={dest_lon}&buffer={buffer}"
    )
    
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error! status: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch cameras: {str(e)}")

# ---------------------------
# Tool: Get Nearest Cameras
# ---------------------------
@mcp.tool()
def get_nearest_cameras(lat: float, lon: float, limit: int = 5):
    """Get nearest cameras to a geo point."""
    # Validate parameters
    if lat is None or lon is None:
        raise ValueError("Missing required parameters: lat, lon")
    if limit is None or limit <= 0:
        raise ValueError("Limit must be greater than 0")
    
    url = (
        f"{BASE_URL}/sse/cameras"
        f"?lat={lat}&lon={lon}&nearest=true&limit={limit}"
    )
    
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error! status: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch cameras: {str(e)}")

# ---------------------------
# Tool: Get Camera Image
# ---------------------------
@mcp.tool()
def get_camera_image(asset_id: str):
    """Return camera image URL for the given asset_id."""
    # Validate parameter
    if not asset_id:
        raise ValueError("Missing required parameter: asset_id")
    
    return {
        "url": f"{BASE_URL}/sse/image?asset_id={asset_id}"
    }

# Start MCP server event loop
if __name__ == "__main__":
    try:
        print("Vancam MCP server running on stdio", file=sys.stderr)
        mcp.run()
    except KeyboardInterrupt:
        print("Server interrupted", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error in main(): {e}", file=sys.stderr)
        sys.exit(1)

