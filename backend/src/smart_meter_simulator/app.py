"""FastAPI application for the GLM grid model simulator."""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from smart_meter_simulator.lifespan import lifespan
from smart_meter_simulator.routers.api_v1 import router as api_v1_router
from smart_meter_simulator.routers.market_ws import router as market_ws_router

load_dotenv(override=True)


def create_app() -> FastAPI:
    app = FastAPI(
        title="GLM Grid Model Simulator",
        description="Smart meter simulation backed by a GridLAB-D GLM topology model.",
        version="6.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_v1_router)
    # Root-level WS (/ws) — APISIX rewrites the public /api/market/ws onto it.
    app.include_router(market_ws_router)
    return app


app = create_app()


def main() -> None:
    port = int(os.getenv("PORT", "8082"))
    uvicorn.run("smart_meter_simulator.app:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
