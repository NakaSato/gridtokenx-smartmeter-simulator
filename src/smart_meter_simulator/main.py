"""
Refactored main application for smart meter simulator.
"""

import sys
import smart_meter_simulator

print(f"DEBUG: smart_meter_simulator file: {smart_meter_simulator.__file__}")
print(f"DEBUG: sys.path: {sys.path}")

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import Settings, load_settings
from .container import configure_container
from .exceptions import SmartMeterSimulatorError
from .api import create_app

logger = logging.getLogger(__name__)


class SmartMeterSimulatorApp:
    """Main application class for smart meter simulator."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the application."""
        self.settings = settings or load_settings()
        self.container = configure_container(self.settings)
        self.app: Optional[FastAPI] = None

        logger.info("SmartMeterSimulatorApp initialized")

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        if self.app is not None:
            return self.app

        # Create FastAPI app using the new API factory
        self.app = create_app()

        # Configure middleware
        self._configure_middleware()

        # Configure health check
        self._configure_health_check()

        # Register lifecycle events
        @self.app.on_event("startup")
        async def startup_event():
            await self.startup()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.shutdown()

        logger.info("FastAPI application created and configured")
        return self.app

    def _configure_middleware(self) -> None:
        """Configure application middleware."""
        if not self.app:
            raise SmartMeterSimulatorError("Application not created")

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.cors_origins,
            allow_credentials=self.settings.cors_allow_credentials,
            allow_methods=self.settings.cors_allow_methods,
            allow_headers=self.settings.cors_allow_headers,
        )

        logger.debug("CORS middleware configured")

    def _configure_health_check(self) -> None:
        """Configure health check endpoint."""
        if not self.app:
            raise SmartMeterSimulatorError("Application not created")

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "version": "2.0.0",
                "container_status": "configured",
                "services": list(self.container._services.keys()),
            }

        logger.debug("Health check endpoint configured")

    async def startup(self) -> None:
        """Application startup logic."""
        try:
            # Start background services
            await self._start_services()

            logger.info("Smart Meter Simulator started successfully")

        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            raise SmartMeterSimulatorError(f"Startup failed: {str(e)}")

    async def shutdown(self) -> None:
        """Application shutdown logic."""
        try:
            # Stop background services
            await self._stop_services()

            logger.info("Smart Meter Simulator shut down successfully")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    async def _start_services(self) -> None:
        """Start background services."""
        # Get services from container
        sim_service = self.container.get(SimulationService)

        # Add default meters if none exist
        if not sim_service.engine.meters:
            logger.info("No meters found. Adding default meters.")
            from .services.meter_service import MeterService
            import uuid

            meter_service = self.container.get(MeterService)

            # Add a Solar Prosumer
            meter_service.add_meter(
                {
                    "meter_id": str(uuid.uuid4()),
                    "meter_type": "Solar_Prosumer",
                    "user_type": "Prosumer",
                    "location": "Building A",
                    "has_solar": True,
                    "has_battery": True,
                    "solar_capacity": 5.0,
                    "battery_capacity": 10.0,
                    "trading_preference": "Moderate",
                }
            )

            # Add a Grid Consumer
            meter_service.add_meter(
                {
                    "meter_id": str(uuid.uuid4()),
                    "meter_type": "Grid_Consumer",
                    "user_type": "Consumer",
                    "location": "Building B",
                    "trading_preference": "Conservative",
                }
            )

        # Start simulation if configured to do so (for now, default to False)
        # TODO: Add auto_start to Settings if needed
        if True:  # self.settings.simulation.auto_start:
            sim_service.start_simulation()

        logger.debug("Background services started")

    async def _stop_services(self) -> None:
        """Stop background services."""
        # Get services from container
        sim_service = self.container.get(SimulationService)

        # Stop simulation
        if sim_service.is_running():
            sim_service.stop_simulation()

        logger.debug("Background services stopped")

    def run(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Run the application."""
        import uvicorn

        # Create app if not already created
        app = self.create_app()

        # Use settings defaults if not provided
        host = host or self.settings.host
        port = port or self.settings.port

        logger.info(f"Starting server on {host}:{port}")

        # Run with uvicorn
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=self.settings.log_level.lower(),
        )


# Import required services for type hints
from .services.simulation_service import SimulationService


def create_application(settings: Optional[Settings] = None) -> SmartMeterSimulatorApp:
    """Factory function to create the application."""
    return SmartMeterSimulatorApp(settings)


def main():
    """Main entry point for the application."""
    import sys

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        # Create and run application
        app = create_application()
        app.run()

    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


# Module-level app instance for uvicorn
# Usage: uvicorn src.smart_meter_simulator.main:app --reload
_application = create_application()
app = _application.create_app()


if __name__ == "__main__":
    main()
