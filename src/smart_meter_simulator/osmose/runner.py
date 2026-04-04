"""
OSMOSE Runner

Main orchestrator for running OSMOSE analysers.
Coordinates data fetching, analyser execution, and result upload.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from .fetcher import OSMOSEDataFetcher, OSMOSEDataCache
from .core.analyser import Analyser, AnalyserSax, AnalyserOsmosis, AnalyserMerge
from .core.plugin import Plugin, PowerPlugin
from .core.issue import OsmoseValidationResult
from .database import OSMOSEDatabase

logger = logging.getLogger(__name__)


class OSMOSERunner:
    """
    Main runner for OSMOSE validation.
    
    Orchestrates:
    - Data fetching from Overpass/PBF
    - Analyser execution
    - Result storage and upload
    - Scheduling and monitoring
    """
    
    def __init__(self, country: str, db_url: Optional[str] = None):
        self.country = country
        self.db_url = db_url
        self.database = OSMOSEDatabase(db_url) if db_url else None
        self.fetcher = OSMOSEDataFetcher()
        self.cache = OSMOSEDataCache(ttl_seconds=3600)
        self.analysers: List[Analyser] = []
        self.plugins: List[Plugin] = []
        self.results: List[OsmoseValidationResult] = []
    
    def register_analyser(self, analyser: Analyser):
        """Register an analyser for execution"""
        self.analysers.append(analyser)
        logger.info(f"Registered analyser: {analyser.analyser_id}")
    
    def register_plugin(self, plugin: Plugin):
        """Register a plugin for SAX analyser"""
        self.plugins.append(plugin)
        logger.info(f"Registered plugin: {plugin.__class__.__name__}")
    
    async def run_all(self, bbox: Optional[Dict[str, float]] = None) -> List[OsmoseValidationResult]:
        """
        Run all registered analysers.
        
        Args:
            bbox: Optional bounding box for data fetch
            
        Returns:
            List of validation results
        """
        logger.info(f"Starting OSMOSE validation for {self.country}")
        start_time = time.time()
        
        # Fetch OSM data
        osm_data = await self._fetch_osm_data(bbox)
        
        # Run each analyser
        for analyser in self.analysers:
            try:
                logger.info(f"Running analyser: {analyser.analyser_id}")
                result = await asyncio.to_thread(analyser.run, osm_data)
                self.results.append(result)
                
                # Store in database if available
                if self.database:
                    await self.database.store_result(result)
                
                logger.info(f"Analyser {analyser.analyser_id} found {result.total_issues} issues")
                
            except Exception as e:
                logger.error(f"Analyser {analyser.analyser_id} failed: {e}")
                continue
        
        total_time = time.time() - start_time
        logger.info(f"Validation complete in {total_time:.2f}s")
        
        return self.results
    
    async def run_analyser(self, analyser_id: str, 
                          bbox: Optional[Dict[str, float]] = None) -> OsmoseValidationResult:
        """
        Run a specific analyser by ID.
        
        Args:
            analyser_id: Analyser identifier
            bbox: Optional bounding box
            
        Returns:
            Validation result
        """
        analyser = next((a for a in self.analysers if a.analyser_id == analyser_id), None)
        if not analyser:
            raise ValueError(f"Analyser {analyser_id} not found")
        
        osm_data = await self._fetch_osm_data(bbox)
        result = await asyncio.to_thread(analyser.run, osm_data)
        
        if self.database:
            await self.database.store_result(result)
        
        return result
    
    async def _fetch_osm_data(self, bbox: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Fetch OSM data with caching"""
        cache_key = f"{self.country}:{bbox}" if bbox else self.country
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("Using cached OSM data")
            return cached
        
        # Fetch from Overpass
        logger.info("Fetching OSM data from Overpass")
        if bbox:
            osm_data = await self.fetcher.fetch_bbox(bbox)
        else:
            # Fetch power infrastructure by default
            osm_data = await self.fetcher.fetch_power_infrastructure(bbox or {})
        
        # Cache the data
        self.cache.set(cache_key, osm_data)
        
        return osm_data
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary"""
        total_issues = sum(r.total_issues for r in self.results)
        total_objects = sum(r.total_objects for r in self.results)
        
        issues_by_level = {"1": 0, "2": 0, "3": 0}
        issues_by_analyser: Dict[str, int] = {}
        
        for result in self.results:
            for level, count in result.issues_by_level.items():
                issues_by_level[level] += count
            issues_by_analyser[result.analyser] = result.total_issues
        
        return {
            "country": self.country,
            "total_analysers": len(self.analysers),
            "total_objects": total_objects,
            "total_issues": total_issues,
            "issues_by_level": issues_by_level,
            "issues_by_analyser": issues_by_analyser,
            "results": [r.to_summary() for r in self.results],
        }
    
    def get_issues(self, level_min: int = 1, level_max: int = 3,
                   bbox: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """
        Get all issues with optional filtering.
        
        Args:
            level_min: Minimum severity level
            level_max: Maximum severity level
            bbox: Optional bounding box filter
            
        Returns:
            List of issue dictionaries
        """
        all_issues = []
        
        for result in self.results:
            # Filter by level
            filtered = result.filter_by_level(level_min, level_max)
            
            # Filter by bbox
            if bbox:
                filtered = filtered.filter_by_bbox(
                    bbox["south"], bbox["north"],
                    bbox["west"], bbox["east"]
                )
            
            all_issues.extend([i.dict() for i in filtered.issues])
        
        return all_issues


class OSMOSEScheduler:
    """
    Scheduler for periodic OSMOSE validation runs.
    """
    
    def __init__(self, runner: OSMOSERunner):
        self.runner = runner
        self.running = False
        self.tasks: List[asyncio.Task] = []
    
    async def start(self, interval_hours: int = 24):
        """Start scheduled validation"""
        self.running = True
        logger.info(f"Starting OSMOSE scheduler (interval: {interval_hours}h)")
        
        while self.running:
            try:
                await self.runner.run_all()
                await asyncio.sleep(interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduled run failed: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        for task in self.tasks:
            task.cancel()
        logger.info("OSMOSE scheduler stopped")


def create_power_runner(country: str = "th", db_url: Optional[str] = None) -> OSMOSERunner:
    """
    Create a runner configured for power infrastructure validation.
    
    Args:
        country: Country code
        db_url: Database URL
        
    Returns:
        Configured OSMOSERunner
    """
    runner = OSMOSERunner(country, db_url)
    
    # Register power plugin
    runner.register_plugin(PowerPlugin())
    
    # Create SAX analyser with power plugin
    sax_analyser = AnalyserSax("power_plugin", country)
    sax_analyser.register_plugin(PowerPlugin())
    runner.register_analyser(sax_analyser)
    
    logger.info("Created power validation runner")
    return runner
