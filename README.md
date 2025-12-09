# Vancam MCP Server

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that provides access to real-time traffic camera data from [Vancam.ai](https://vancam.ai).

## Features

- 🔍 **Search cameras** by radius, route, bounds, or nearest location
- 📸 **Get camera images** by asset ID
- 🌐 **Real-time data** from traffic cameras across North America
- 🤖 **AI-ready** - Designed for use with AI agents and assistants

## Usage

The Vancam GPT is available in the [GPT Store](#gpt-store) for use with ChatGPT.

**Claude MCP Server:** Coming soon - This remote MCP server will connect to the Vancam.ai API. No local installation or dependencies will be required.

## Available Tools

### `list_cameras`
List all cameras within a bounding box.

**Parameters:**
- `min_lat` (float): Minimum latitude
- `min_lon` (float): Minimum longitude
- `max_lat` (float): Maximum latitude
- `max_lon` (float): Maximum longitude

**Example:**
```python
list_cameras(min_lat=49.2, min_lon=-123.2, max_lat=49.3, max_lon=-123.0)
```

### `get_cameras_by_radius`
Get cameras within a specified radius around a geographic point.

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude
- `radius` (float, optional): Radius in kilometers (default: 1.0)

**Example:**
```python
get_cameras_by_radius(lat=49.28, lon=-123.12, radius=1.0)
```

### `get_cameras_along_route`
Get cameras along a route between two points.

**Parameters:**
- `origin_lat` (float): Origin latitude
- `origin_lon` (float): Origin longitude
- `dest_lat` (float): Destination latitude
- `dest_lon` (float): Destination longitude
- `buffer` (float, optional): Buffer distance in meters (default: 100.0)

**Example:**
```python
get_cameras_along_route(
    origin_lat=49.28, origin_lon=-123.12,
    dest_lat=49.30, dest_lon=-123.09,
    buffer=100.0
)
```

### `get_nearest_cameras`
Get the nearest cameras to a geographic point.

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude
- `limit` (int, optional): Maximum number of cameras to return (default: 5)

**Example:**
```python
get_nearest_cameras(lat=49.28, lon=-123.12, limit=5)
```

### `get_camera_image`
Get the URL for a camera image by asset ID.

**Parameters:**
- `asset_id` (string): Camera asset ID

**Example:**
```python
get_camera_image(asset_id="123")
```

## API Reference

The underlying API is documented in OpenAPI format. See `openapi.yaml` for complete API documentation.

**Base URL:** `https://vancam.ai`

**Endpoints:**
- `GET /sse/cameras` - Search for cameras
- `GET /sse/image?asset_id={id}` - Get camera image

## Examples

### Finding cameras near Vancouver
```python
# Get 5 nearest cameras to downtown Vancouver
get_nearest_cameras(lat=49.2827, lon=-123.1207, limit=5)
```

### Finding cameras along a route
```python
# Cameras along Highway 99 from Vancouver to Richmond
get_cameras_along_route(
    origin_lat=49.2827, origin_lon=-123.1207,
    dest_lat=49.1666, dest_lon=-123.1367,
    buffer=200.0
)
```

### Getting a camera image
```python
# Get image URL for a specific camera
result = get_camera_image(asset_id="12345")
image_url = result["url"]
```

## Project Structure

```
mcp-vancam/
├── server.py          # MCP server implementation
├── openapi.yaml       # API specification
└── README.md          # This file
```

## Related Projects

- [Vancam.ai](https://vancam.ai/mcp) - Web interface for traffic cameras
- [Model Context Protocol](https://modelcontextprotocol.io) - MCP specification

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Open an issue on GitHub
- Visit [Vancam.ai](https://vancam.ai)

## GPT Store

### Vancam

The Vancam MCP server is available in the GPT Store as a ChatGPT GPT:

- **GPT Store:** [Vancam GPT](https://chatgpt.com/g/g-693512b18c0481918eb9b2c5d77e9eaa-vancam)
- **Name:** "vancam"
- **Description:** Access real-time traffic camera data from Vancam.ai. Search cameras by location, radius, route, or get the nearest cameras to any point. Perfect for checking traffic conditions, planning routes, or monitoring road conditions across North America.





