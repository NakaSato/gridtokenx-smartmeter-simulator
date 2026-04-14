#!/usr/bin/env python3
"""
Fetch real power grid infrastructure from OSM via Overpass API.

Layers:
- powerline (transmission lines with voltage)
- power tower / pole (support structures)
- substation (transformer stations)
- generator (power plants)

Area: Thailand coverage (bounding box)
"""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Thailand bounding box (approx)
THAILAND_BBOX = "13.7,100.5,14.0,102.5"  # lat_min,lon_min,lat_max,lon_max

# Overpass QL query for power infrastructure
OVERPASS_QUERY = f"""
[out:json][timeout:600];
(
  // Power lines
  way["power"="line"]({THAILAND_BBOX});
  way["power"="cable"]({THAILAND_BBOX});
  way["power"="minor_line"]({THAILAND_BBOX});

  // Power towers and poles
  node["power"="tower"]({THAILAND_BBOX});
  node["power"="pole"]({THAILAND_BBOX});

  // Substations
  node["power"="substation"]({THAILAND_BBOX});
  way["power"="substation"]({THAILAND_BBOX});
  relation["power"="substation"]({THAILAND_BBOX});

  // Generators (power plants)
  node["power"="generator"]({THAILAND_BBOX});
  way["power"="generator"]({THAILAND_BBOX});

  // Power plants (plant areas)
  way["power"="plant"]({THAILAND_BBOX});
  relation["power"="plant"]({THAILAND_BBOX});
);
out body geom;
>;
out skel qt;
"""


async def fetch_overpass():
    """Fetch power grid data from Overpass API"""
    import aiohttp

    logger.info(f"Fetching from Overpass API: {OVERPASS_URL}")
    logger.info(f"Query length: {len(OVERPASS_QUERY)} chars")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            OVERPASS_URL,
            data={"data": OVERPASS_QUERY},
            timeout=aiohttp.ClientTimeout(total=600),
        ) as resp:
            if resp.status != 200:
                logger.error(f"Overpass returned {resp.status}")
                return None
            return await resp.json()


def convert_to_geojson(data: dict) -> dict:
    """Convert Overpass response to GeoJSON FeatureCollection"""
    features = []

    nodes = {n["id"]: n for n in data.get("elements", []) if n["type"] == "node"}

    for elem in data.get("elements", []):
        if elem["type"] == "node":
            tags = elem.get("tags", {})
            if not tags.get("power"):
                continue

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [elem.get("lon", 0), elem.get("lat", 0)],
                },
                "properties": {
                    "osm_id": f"n{elem['id']}",
                    "osm_type": "node",
                    **{k: str(v) for k, v in tags.items()},
                },
            })

        elif elem["type"] == "way":
            tags = elem.get("tags", {})
            if not tags.get("power"):
                continue

            # Build LineString from node refs or embedded geometry
            coords = []
            if "geometry" in elem:
                coords = [[p.get("lon", 0), p.get("lat", 0)] for p in elem["geometry"]]
            else:
                # Try to resolve node references
                for nid in elem.get("nodes", []):
                    if nid in nodes:
                        n = nodes[nid]
                        coords.append([n.get("lon", 0), n.get("lat", 0)])

            if len(coords) < 2:
                continue

            geom_type = "LineString" if tags.get("power") in ("line", "cable", "minor_line") else "Polygon"

            if geom_type == "Polygon" and coords[0] != coords[-1]:
                coords.append(coords[0])  # Close ring

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": geom_type,
                    "coordinates": coords,
                },
                "properties": {
                    "osm_id": f"w{elem['id']}",
                    "osm_type": "way",
                    **{k: str(v) for k, v in tags.items()},
                },
            })

        elif elem["type"] == "relation":
            tags = elem.get("tags", {})
            if not tags.get("power"):
                continue

            # Extract outer ring from members
            outer_coords = []
            for member in elem.get("members", []):
                if member["type"] == "node" and "lat" in member:
                    outer_coords.append([member.get("lon", 0), member.get("lat", 0)])
                elif member["type"] == "way" and "geometry" in member:
                    for p in member["geometry"]:
                        outer_coords.append([p.get("lon", 0), p.get("lat", 0)])

            if len(outer_coords) < 3:
                continue

            # Close ring
            if outer_coords[0] != outer_coords[-1]:
                outer_coords.append(outer_coords[0])

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [outer_coords],
                },
                "properties": {
                    "osm_id": f"r{elem['id']}",
                    "osm_type": "relation",
                    **{k: str(v) for k, v in tags.items()},
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


async def main():
    data = await fetch_overpass()
    if not data:
        logger.error("Failed to fetch Overpass data")
        return

    geojson = convert_to_geojson(data)
    logger.info(f"Converted {len(geojson['features'])} features to GeoJSON")

    # Save to file
    out_path = Path(__file__).parent / "data" / "thailand_power_grid.geojson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved to {out_path} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # Summary by type
    types = {}
    for feat in geojson["features"]:
        pwr = feat["properties"].get("power", "unknown")
        types[pwr] = types.get(pwr, 0) + 1

    print("\n=== Feature Summary ===")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")
    print(f"  TOTAL: {len(geojson['features'])}")


if __name__ == "__main__":
    asyncio.run(main())
