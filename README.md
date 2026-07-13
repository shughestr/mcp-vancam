# Vancam MCP Server

[Vancam.ai](https://vancam.ai) — **Traffic Cameras & Road Conditions** — as an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server. Gives AI agents live access to the same camera network behind Vancam's road-condition data: over 1 million traffic cameras worldwide, searchable by map bounds, radius, route, or nearest point.

- 🔍 **Search cameras** by bounding box, radius, route corridor, or nearest-to-point
- 📸 **Fetch live frames** by camera asset ID, returned directly in the tool result
- 🌐 **Real-time data** from the same backend that powers the [Vancam.ai](https://vancam.ai) map
- 🤖 **AI-ready** — built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk), works with Claude Desktop, Claude Code, and any MCP-compatible client

## Quick Start

**1. Clone and install dependencies**

```bash
git clone https://github.com/<your-org>/mcp-vancam.git
cd mcp-vancam
pip install -r requirements.txt
```

**2. (Optional) Set up an API key**

Requests work out of the box using a shared, rate-limited key (1 req/s, 500/month, pooled across all anonymous users). For higher limits, grab a free personal key from your [Vancam.ai account page](https://vancam.ai) and set it as an environment variable:

```bash
cp .env.example .env   # then edit .env
```

```bash
# .env
VANCAM_API_KEY=your_personal_key_here
```

**3. Register the server with your MCP client**

For Claude Desktop or Claude Code, add to your MCP config (see `.mcp.json` in this repo for a working example):

```json
{
  "mcpServers": {
    "vancam": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-vancam/server.py"],
      "env": {
        "VANCAM_API_KEY": ""
      }
    }
  }
}
```

`VANCAM_API_KEY` is optional — leave it blank to use the shared, rate-limited key.

Restart your client, and the tools below become available.

## Available Tools

### `list_cameras`
List cameras within a bounding box — the same query the VanCam map runs on pan/zoom.

```python
list_cameras(min_lat=49.2, min_lon=-123.2, max_lat=49.3, max_lon=-123.0, limit=50)
```
| Parameter | Type | Description |
|---|---|---|
| `min_lat`, `min_lon`, `max_lat`, `max_lon` | float | Bounding box (WGS84) |
| `limit` | int, optional | Max results, 1–100 (default 100) |
| `active_only` | bool, optional | Only `camera_class=open` live feeds (default false) |

### `get_cameras_by_radius`
Get cameras within a radius of a point.

```python
get_cameras_by_radius(lat=49.28, lon=-123.12, radius=1.0, limit=20)
```
| Parameter | Type | Description |
|---|---|---|
| `lat`, `lon` | float | Center point (WGS84) |
| `radius` | float, optional | Radius in km (default 1.0) |
| `limit` | int, optional | Max results (default 50) |
| `active_only` | bool, optional | Only open/live cameras |

### `get_cameras_along_route`
Get cameras along a straight-line corridor between two points.

```python
get_cameras_along_route(
    origin_lat=49.2827, origin_lon=-123.1207,
    dest_lat=49.1666, dest_lon=-123.1367,
    buffer=200.0, limit=50
)
```
| Parameter | Type | Description |
|---|---|---|
| `origin_lat`, `origin_lon`, `dest_lat`, `dest_lon` | float | Route endpoints |
| `buffer` | float, optional | Corridor width in meters (default 100.0) |
| `limit` | int, optional | Max results (default 50) |
| `active_only` | bool, optional | Only open/live cameras |

Results are sorted by `route_fraction` (0 = origin, 1 = destination). Note: this is a straight line between the two points, not a driving route.

### `get_nearest_cameras`
Get the closest cameras to a point.

```python
get_nearest_cameras(lat=49.2827, lon=-123.1207, limit=5)
```
| Parameter | Type | Description |
|---|---|---|
| `lat`, `lon` | float | Query point (WGS84) |
| `limit` | int, optional | Number of cameras (default 5) |
| `active_only` | bool, optional | Only open/live cameras |

### `get_camera_image`
Fetch a camera's live frame by asset ID, returned as image data in the tool result (not just a URL — the image endpoint requires an API key header that most MCP clients can't attach themselves).

```python
get_camera_image(asset_id="30145")
```

### `describe_camera_api`
Returns documentation for all search modes, camera fields, and image URL patterns. Call this first if you're unsure which tool to use.

## API Reference

Every search tool queries the same spatial API that backs the [Vancam.ai](https://vancam.ai) map:

| Purpose | URL |
|---|---|
| Spatial search | `https://api.vancam.ai/cameras/cameras` |
| Live image | `https://api.vancam.ai/api?asset_id={id}` |

Each camera includes `asset_id`, `latitude`, `longitude`, `street_address`, `direction`, `camera_class` (`open`/`premium`), `level1`/`level2`/`level3` (country/state/city), `distance_meters` (radius/nearest searches), `route_fraction` (route search), and `image_url`/`image_urls`.

Full schema: [`openapi.yaml`](openapi.yaml).

**Environment overrides:** `VANCAM_API_KEY`, `VANCAM_CAMERAS_SEARCH_URL`, `VANCAM_API_IMAGE_URL`

## Project Structure

```
mcp-vancam/
├── server.py         # MCP server — registers the tools above
├── camera_api.py     # api.vancam.ai client
├── openapi.yaml       # API specification
├── requirements.txt  # Python dependencies
└── .mcp.json         # Example MCP client config
```

## Related Projects

- [Vancam.ai](https://vancam.ai) — Web interface for traffic cameras
- [Model Context Protocol](https://modelcontextprotocol.io) — MCP specification
- [Vancam GPT](https://chatgpt.com/g/g-693512b18c0481918eb9b2c5d77e9eaa-vancam) — Same data, packaged as a ChatGPT GPT

## Contributing

Contributions are welcome — feel free to open an issue or submit a pull request.

## License

MIT — see [LICENSE](LICENSE).
