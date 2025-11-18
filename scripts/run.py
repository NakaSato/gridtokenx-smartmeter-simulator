#!/usr/bin/env python3
"""
Run script for Smart Meter Simulator
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "smart_meter_simulator.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )