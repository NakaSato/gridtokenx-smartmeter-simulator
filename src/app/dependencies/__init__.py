"""
Dependency injection container for the Smart Meter Simulator.
"""

from .container import DIContainer, get_container, init_container

__all__ = [
    "DIContainer",
    "get_container", 
    "init_container",
]
