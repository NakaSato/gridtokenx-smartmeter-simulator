"""
OSMOSE QA Integration Module - GridTokenX Smart Meter Simulator

Complete integration of OSMOSE Quality Assurance system for OpenStreetMap validation
and electrical infrastructure quality checking.

This module provides GridTokenX custom extensions for:
- Power infrastructure validation (substations, power lines, generators)
- Thai grid integration (EGAT, MEA, PEA networks)
- Smart meter data quality assurance
- Spatial conflation and matching
- Batch analytics pipeline

Components:
-----------
  - core/ : Custom analysers and plugins
  - utils/ : Spatial utilities and conflation
  - grid_quality.py : Quality management system
  - tile_server.py : Vector tile serving
  - dataset.py : Sample datasets and test generation
  - runner.py : Async OSMOSE runner
  - fetcher.py : Data fetching utilities
  - database.py : PostgreSQL integration

Usage:
------
# High-level API
from smart_meter_simulator.osmose import (
    GridQualityManager,
    OSMOSERunner,
    create_power_runner,
)

runner = create_power_runner(country="thailand")
results = await runner.run_all()

# Core classes
from smart_meter_simulator.osmose.core import Analyser, AnalyserSax

# Spatial utilities
from smart_meter_simulator.osmose.utils import SpatialMatcher, ConflationConfig
"""

__version__ = "3.0.0"
__merge_date__ = "2026-04-04"

# Lazy loading via __getattr__ to prevent eager import failures
# This allows partial imports even if some dependencies are missing

__all__ = [
    # Core classes
    "OsmoseIssue",
    "IssueLevel",
    "IssueCategory",
    "OsmoseValidationResult",
    "Analyser",
    "AnalyserOsmosis",
    "AnalyserMerge",
    "AnalyserSax",
    "Plugin",
    "PluginMapCSS",
    "PowerPlugin",
    # Analytics
    "BatchAnalyticsPipeline",
    "AnalyticsType",
    "AnalyticsJob",
    "DailyAnalyticsResult",
    "AnomalyReport",
    # Integration
    "OSMOSEDataFetcher",
    "OSMOSERunner",
    "create_power_runner",
    "OSMOSEDatabase",
    "OSMOSEVectorTileServer",
    # Spatial
    "SpatialMatcher",
    "ConflationConfig",
    "SpatialMatch",
    "BoundingBoxFilter",
    "create_thailand_bbox",
    "create_bangkok_bbox",
    # Analysers
    "PowerSubstationValidator",
    "PowerLineConnectivity",
    "DuplicateDetection",
    "MeterConflation",
    "MeterMatch",
    "GridQualityConfig",
    # Quality Management
    "GridQualityManager",
    "GridQualityMonitor",
    "GridQualityScore",
    "create_quality_manager",
    # Datasets
    "OSMOSEDataset",
    "get_sample",
    "generate_test",
]


def __getattr__(name: str):
    """Lazy-load module attributes to prevent import-time failures."""
    # Core classes
    if name == "OsmoseIssue":
        from .core.issue import OsmoseIssue
        return OsmoseIssue
    if name == "IssueLevel":
        from .core.issue import IssueLevel
        return IssueLevel
    if name == "IssueCategory":
        from .core.issue import IssueCategory
        return IssueCategory
    if name == "OsmoseValidationResult":
        from .core.issue import OsmoseValidationResult
        return OsmoseValidationResult

    if name == "Analyser":
        from .core.analyser import Analyser
        return Analyser
    if name == "AnalyserOsmosis":
        from .core.analyser import AnalyserOsmosis
        return AnalyserOsmosis
    if name == "AnalyserMerge":
        from .core.analyser import AnalyserMerge
        return AnalyserMerge
    if name == "AnalyserSax":
        from .core.analyser import AnalyserSax
        return AnalyserSax

    if name == "Plugin":
        from .core.plugin import Plugin
        return Plugin
    if name == "PluginMapCSS":
        from .core.plugin import PluginMapCSS
        return PluginMapCSS
    if name == "PowerPlugin":
        from .core.plugin import PowerPlugin
        return PowerPlugin

    # Analytics
    if name == "BatchAnalyticsPipeline":
        from .core.batch_analytics import BatchAnalyticsPipeline
        return BatchAnalyticsPipeline
    if name == "AnalyticsType":
        from .core.batch_analytics import AnalyticsType
        return AnalyticsType
    if name == "AnalyticsJob":
        from .core.batch_analytics import AnalyticsJob
        return AnalyticsJob
    if name == "DailyAnalyticsResult":
        from .core.batch_analytics import DailyAnalyticsResult
        return DailyAnalyticsResult
    if name == "AnomalyReport":
        from .core.batch_analytics import AnomalyReport
        return AnomalyReport

    # Integration
    if name == "OSMOSEDataFetcher":
        from .fetcher import OSMOSEDataFetcher
        return OSMOSEDataFetcher
    if name == "OSMOSERunner":
        from .runner import OSMOSERunner
        return OSMOSERunner
    if name == "create_power_runner":
        from .runner import create_power_runner
        return create_power_runner
    if name == "OSMOSEDatabase":
        from .database import OSMOSEDatabase
        return OSMOSEDatabase
    if name == "OSMOSEVectorTileServer":
        from .tile_server import OSMOSEVectorTileServer
        return OSMOSEVectorTileServer

    # Spatial
    if name == "SpatialMatcher":
        from .utils.spatial import SpatialMatcher
        return SpatialMatcher
    if name == "ConflationConfig":
        from .utils.spatial import ConflationConfig
        return ConflationConfig
    if name == "SpatialMatch":
        from .utils.spatial import SpatialMatch
        return SpatialMatch
    if name == "BoundingBoxFilter":
        from .utils.spatial import BoundingBoxFilter
        return BoundingBoxFilter
    if name == "create_thailand_bbox":
        from .utils.spatial import create_thailand_bbox
        return create_thailand_bbox
    if name == "create_bangkok_bbox":
        from .utils.spatial import create_bangkok_bbox
        return create_bangkok_bbox

    # Analysers
    if name == "PowerSubstationValidator":
        from .analysers.power_substation import PowerSubstationValidator
        return PowerSubstationValidator
    if name == "PowerLineConnectivity":
        from .analysers.power_line_connectivity import PowerLineConnectivity
        return PowerLineConnectivity
    if name == "DuplicateDetection":
        from .analysers.duplicate_detection import DuplicateDetection
        return DuplicateDetection
    if name == "MeterConflation":
        from .analysers.meter_conflation import MeterConflation
        return MeterConflation
    if name == "MeterMatch":
        from .analysers.meter_conflation import MeterMatch
        return MeterMatch
    if name == "GridQualityConfig":
        from .grid_quality import GridQualityConfig
        return GridQualityConfig

    # Quality Management
    if name == "GridQualityManager":
        from .grid_quality import GridQualityManager
        return GridQualityManager
    if name == "GridQualityMonitor":
        from .grid_quality import GridQualityMonitor
        return GridQualityMonitor
    if name == "GridQualityScore":
        from .grid_quality import GridQualityScore
        return GridQualityScore
    if name == "create_quality_manager":
        from .grid_quality import create_quality_manager
        return create_quality_manager

    # Datasets
    if name == "OSMOSEDataset":
        from .dataset import OSMOSEDataset
        return OSMOSEDataset
    if name == "get_sample":
        from .dataset import get_sample
        return get_sample
    if name == "generate_test":
        from .dataset import generate_test
        return generate_test

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
