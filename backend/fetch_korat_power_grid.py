#!/usr/bin/env python3
"""
Fetch power grid infrastructure for Nakhon Ratchasima (Korat) area from OSM.

Center: 13.9536°N, 101.8508°E (from flosm.org URL)
Radius: ~20.7 km

Specifically fetches way 402761973 and surrounding infrastructure.
"""

import asyncio
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Nakhon Ratchasima bounding box (~20km radius around center)
KORAT_BBOX = "13.77,101.67,14.13,102.03"  # lat_min,lon_min,lat_max,lon_max

# Specific way query
WAY_QUERY = """[out:json];way(402761973);out tags geom;"""

# Full area query - comprehensive power infrastructure
AREA_QUERY = f"""
[out:json][timeout:120];
(
  // Transmission/distribution lines
  way["power"="line"]({KORAT_BBOX});
  way["power"="cable"]({KORAT_BBOX});
  way["power"="minor_line"]({KORAT_BBOX});

  // Support structures
  node["power"="tower"]({KORAT_BBOX});
  node["power"="pole"]({KORAT_BBOX});

  // Substations (with substation type)
  node["power"="substation"]({KORAT_BBOX});
  way["power"="substation"]({KORAT_BBOX});

  // Transformers
  node["power"="transformer"]({KORAT_BBOX});

  // Generators & plants
  node["power"="generator"]({KORAT_BBOX});
  way["power"="generator"]({KORAT_BBOX});
  way["power"="plant"]({KORAT_BBOX});

  // Switchgear, switches, terminals, portals
  node["power"="switch"]({KORAT_BBOX});
  node["power"="terminal"]({KORAT_BBOX});
  node["power"="portal"]({KORAT_BBOX});
  node["power"="insulator"]({KORAT_BBOX});
);
out body geom;
>;
out skel qt;
"""


async def fetch_overpass(query: str, label: str = "query"):
    """Fetch from Overpass API with retry logic"""
    import aiohttp

    logger.info(f"Fetching {label} from Overpass API")

    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OVERPASS_URL,
                    data={"data": query},
                    timeout=aiohttp.ClientTimeout(total=180),
                ) as resp:
                    if resp.status == 429:
                        wait = 30 * (attempt + 1)
                        logger.warning(f"Rate limited (429). Waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    if resp.status != 200:
                        logger.error(f"Overpass returned {resp.status}")
                        return None
                    return await resp.json()
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                await asyncio.sleep(10)

    return None


def extract_way_info(data: dict) -> dict:
    """Extract way tags and geometry"""
    for elem in data.get("elements", []):
        if elem.get("type") == "way" and elem.get("id") == 402761973:
            return {
                "osm_id": 402761973,
                "tags": elem.get("tags", {}),
                "geometry": elem.get("geometry", []),
                "nodes": elem.get("nodes", []),
            }
    return {}


async def main():
    out_dir = Path(__file__).parent / "data" / "korat"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fetch specific way
    logger.info("=== Fetching OSM Way 402761973 ===")
    way_data = await fetch_overpass(WAY_QUERY, "way 402761973")
    if way_data:
        way_info = extract_way_info(way_data)
        out_path = out_dir / "way_402761973.json"
        with open(out_path, "w") as f:
            json.dump(way_info, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {out_path}")
        print(f"\n=== Way 402761973 Tags ===")
        for k, v in way_info.get("tags", {}).items():
            print(f"  {k}: {v}")
        coords = way_info.get("geometry", [])
        print(f"  Points: {len(coords)}")
    else:
        logger.error("Failed to fetch way 402761973 - still rate limited")

    # 2. Fetch full area
    logger.info("\n=== Fetching Korat Power Grid ===")
    area_data = await fetch_overpass(AREA_QUERY, "Korat area")
    if area_data:
        out_path = out_dir / "korat_power_grid.json"
        with open(out_path, "w") as f:
            json.dump(area_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {out_path}")

        # Summary
        types = {}
        for elem in area_data.get("elements", []):
            pwr = elem.get("tags", {}).get("power", "unknown")
            types[pwr] = types.get(pwr, 0) + 1

        print("\n=== Feature Summary ===")
        for t, c in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {c}")
        print(f"  TOTAL: {sum(types.values())}")
    else:
        logger.error("Failed to fetch Korat area data")


if __name__ == "__main__":
    asyncio.run(main())
