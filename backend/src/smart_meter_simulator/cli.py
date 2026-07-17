"""Command line entry point for the GLM grid model simulator."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os

import uvicorn

from smart_meter_simulator.config import get_config
from smart_meter_simulator.core.engine import SimulationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_topology(topology_spec: str) -> int:
    from smart_meter_simulator.core.topology_factory import load_topology_spec

    try:
        topology = load_topology_spec(topology_spec)
        validation = topology.validate()
        print(json.dumps(topology.summary(include_validation=True), indent=2))
        return 0 if validation.is_valid else 1
    except Exception as exc:
        print(
            json.dumps(
                {
                    "source": "glm",
                    "source_path": topology_spec,
                    "validation": {
                        "is_valid": False,
                        "errors": [str(exc)],
                        "warnings": [],
                    },
                },
                indent=2,
            )
        )
        return 1


async def run_standalone(num_meters: int) -> None:
    config = get_config()
    logger.info(
        "Starting standalone GLM simulation: meters=%s topology=%s",
        num_meters,
        config.grid_topology,
    )
    engine = SimulationEngine(
        grid_topology=config.grid_topology,
        num_meters=num_meters,
    )

    try:
        await engine.start()
        while engine.running:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Simulation interrupted")
    finally:
        await engine.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="GLM grid model simulator CLI")
    parser.add_argument(
        "--mode",
        choices=["server", "standalone", "validate-topology"],
        default="server",
        help="Run mode",
    )
    parser.add_argument("--meters", type=int, default=20, help="Number of meters")
    parser.add_argument(
        "--grid-topology",
        default=None,
        help="Topology source spec, e.g. glm:src/smart_meter_simulator/data/grids/rural_reference_80bus.glm",
    )
    parser.add_argument("--port", type=int, default=8082, help="Server port")
    parser.add_argument("--interval", type=int, help="Simulation interval in seconds")
    parser.add_argument("--base-gen-min", type=float, help="Minimum generation kW")
    parser.add_argument("--base-gen-max", type=float, help="Maximum generation kW")
    parser.add_argument("--base-cons-min", type=float, help="Minimum consumption kW")
    parser.add_argument("--base-cons-max", type=float, help="Maximum consumption kW")

    args = parser.parse_args()

    if args.grid_topology:
        os.environ["GRID_TOPOLOGY"] = args.grid_topology
    os.environ["NUM_METERS"] = str(args.meters)
    os.environ["PORT"] = str(args.port)

    for value, env_name in [
        (args.interval, "SIMULATION_INTERVAL"),
        (args.base_gen_min, "BASE_GENERATION_MIN"),
        (args.base_gen_max, "BASE_GENERATION_MAX"),
        (args.base_cons_min, "BASE_CONSUMPTION_MIN"),
        (args.base_cons_max, "BASE_CONSUMPTION_MAX"),
    ]:
        if value is not None:
            os.environ[env_name] = str(value)

    if args.mode == "validate-topology":
        config = get_config()
        raise SystemExit(validate_topology(args.grid_topology or config.grid_topology))

    if args.mode == "server":
        uvicorn.run(
            "smart_meter_simulator.app:app",
            host="0.0.0.0",
            port=args.port,
            reload=False,
        )
        return

    asyncio.run(run_standalone(args.meters))


if __name__ == "__main__":
    main()
