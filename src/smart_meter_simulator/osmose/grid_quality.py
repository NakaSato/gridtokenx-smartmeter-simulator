"""
Grid Quality Manager

Integration layer between Osmose QA system and Smart Meter Simulator.
Provides:
- Grid infrastructure validation
- Meter-to-infrastructure conflation
- Quality scoring and reporting
- Real-time validation during simulation

Usage:
    from smart_meter_simulator.osmose.grid_quality import GridQualityManager
    
    manager = GridQualityManager()
    
    # Validate grid infrastructure
    result = await manager.validate_infrastructure()
    
    # Get quality score
    score = manager.get_quality_score()
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
import asyncio

from .analysers.power_substation import PowerSubstationValidator
from .analysers.power_line_connectivity import PowerLineConnectivity
from .analysers.duplicate_detection import DuplicateDetection
from .analysers.meter_conflation import MeterConflation, MeterMatch, ConflationConfig
from .core.batch_analytics import BatchAnalyticsPipeline, DailyAnalyticsResult
from .core.issue import OsmoseValidationResult, IssueLevel
from .utils.spatial import SpatialMatcher

logger = logging.getLogger(__name__)


class GridQualityConfig:
    """Configuration for grid quality validation."""
    def __init__(
        self,
        conflation_distance_m: float = 50.0,
        max_pole_distance_m: float = 50.0,
        suspicious_distance_m: float = 200.0,
        pole_duplicate_dist_m: float = 5.0,
        transformer_duplicate_dist_m: float = 5.0,
        substation_duplicate_dist_m: float = 10.0,
        country: str = "TH",
    ):
        self.conflation_distance_m = conflation_distance_m
        self.max_pole_distance_m = max_pole_distance_m
        self.suspicious_distance_m = suspicious_distance_m
        self.pole_duplicate_dist_m = pole_duplicate_dist_m
        self.transformer_duplicate_dist_m = transformer_duplicate_dist_m
        self.substation_duplicate_dist_m = substation_duplicate_dist_m
        self.country = country

    @property
    def conflation_config(self) -> ConflationConfig:
        return ConflationConfig(
            max_pole_distance_m=self.conflation_distance_m,
            max_substation_distance_m=100.0,
            max_transformer_distance_m=30.0,
            suspicious_distance_m=self.suspicious_distance_m,
        )


class GridQualityScore:
    """
    Grid quality scoring system.
    
    Calculates overall grid quality based on:
    - Infrastructure completeness (30%)
    - Data accuracy (30%)
    - Meter alignment (20%)
    - Temporal consistency (20%)
    """
    
    def __init__(self):
        self.infrastructure_score = 100.0
        self.accuracy_score = 100.0
        self.alignment_score = 100.0
        self.consistency_score = 100.0
    
    def calculate_overall(self) -> float:
        """Calculate overall quality score (0-100)"""
        return (
            0.30 * self.infrastructure_score +
            0.30 * self.accuracy_score +
            0.20 * self.alignment_score +
            0.20 * self.consistency_score
        )
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'overall': self.calculate_overall(),
            'infrastructure': self.infrastructure_score,
            'accuracy': self.accuracy_score,
            'alignment': self.alignment_score,
            'consistency': self.consistency_score,
        }
    
    def update_from_issues(self, validation_result: OsmoseValidationResult):
        """Update scores based on validation issues"""
        if not validation_result or validation_result.total_issues == 0:
            return
        
        total = validation_result.total_objects
        if total == 0:
            return
        
        # Count issues by severity
        level1_count = validation_result.issues_by_level.get('1', 0)
        level2_count = validation_result.issues_by_level.get('2', 0)
        level3_count = validation_result.issues_by_level.get('3', 0)
        
        # Weighted penalty
        penalty = (level1_count * 0.1 + level2_count * 0.05 + level3_count * 0.02) / total * 100
        
        # Update accuracy score
        self.accuracy_score = max(0, 100 - penalty)


class GridQualityManager:
    """
    Manager for grid quality validation and monitoring.

    Integrates OSMOSE QA analysers with the Smart Meter Simulator to:
    1. Validate grid infrastructure against OSM data
    2. Match meters to physical infrastructure
    3. Calculate quality scores
    4. Run batch analytics
    5. Generate quality reports

    Analysers:
    - PowerSubstationValidator: Validates substation tags & connectivity
    - PowerLineConnectivity: Validates power line topology
    - DuplicateDetection: Finds duplicate infrastructure elements
    - MeterConflation: Matches simulator meters to OSM infrastructure
    """

    def __init__(self, config: Optional[GridQualityConfig] = None,
                 db_url: Optional[str] = None):
        """
        Initialize grid quality manager.

        Args:
            config: Grid quality configuration
            db_url: Database URL for batch analytics
        """
        self.config = config or GridQualityConfig()

        # Initialize analysers (lazily - they need OSM data)
        self._substation_analyser: Optional[PowerSubstationValidator] = None
        self._line_analyser: Optional[PowerLineConnectivity] = None
        self._duplicate_analyser: Optional[DuplicateDetection] = None
        self._conflation_analyser: Optional[MeterConflation] = None

        # Infrastructure cache
        self._infrastructure_loaded = False
        self._osm_data: Optional[Dict[str, Any]] = None

        # Batch analytics
        self.batch_analytics = BatchAnalyticsPipeline(db_url) if db_url else None

        # Spatial matcher
        self.spatial_matcher = SpatialMatcher()

        # Quality scores
        self.quality_score = GridQualityScore()

        # Validation history
        self.validation_results: Dict[str, OsmoseValidationResult] = {}
        self.last_validation: Optional[datetime] = None
    
    async def validate_infrastructure(self, osm_data: Optional[Dict[str, Any]] = None) -> OsmoseValidationResult:
        """
        Validate grid infrastructure using all analysers.

        Runs:
        - PowerSubstationValidator
        - PowerLineConnectivity
        - DuplicateDetection

        Args:
            osm_data: OSM data dict (if None, fetched automatically)

        Returns:
            Combined OsmoseValidationResult from all analysers
        """
        logger.info("Running infrastructure validation")

        if not osm_data:
            osm_data = await self._fetch_osm_data()
        self._osm_data = osm_data

        # Run substation validator
        self._substation_analyser = PowerSubstationValidator(
            country=self.config.country,
            power_lines=self._extract_power_lines(osm_data),
        )
        sub_result = self._substation_analyser.run(osm_data)

        # Run line connectivity
        self._line_analyser = PowerLineConnectivity(country=self.config.country)
        line_result = self._line_analyser.run(osm_data)

        # Run duplicate detection
        self._duplicate_analyser = DuplicateDetection(
            country=self.config.country,
            pole_dist_m=self.config.pole_duplicate_dist_m,
            transformer_dist_m=self.config.transformer_duplicate_dist_m,
            substation_dist_m=self.config.substation_duplicate_dist_m,
        )
        dup_result = self._duplicate_analyser.run(osm_data)

        # Combine results
        all_issues = sub_result.issues + line_result.issues + dup_result.issues
        total_objects = max(sub_result.total_objects, line_result.total_objects, dup_result.total_objects)

        # Update issue counts
        issues_by_level = {"1": 0, "2": 0, "3": 0}
        issues_by_item: Dict[str, int] = {}
        issues_by_tag: Dict[str, int] = {}
        for issue in all_issues:
            issues_by_level[str(issue.level)] += 1
            item_key = str(issue.item)
            issues_by_item[item_key] = issues_by_item.get(item_key, 0) + 1
            for tag in issue.tags:
                issues_by_tag[tag] = issues_by_tag.get(tag, 0) + 1

        combined = OsmoseValidationResult(
            analyser="combined_infrastructure",
            country=self.config.country,
            timestamp=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            total_objects=total_objects,
            total_issues=len(all_issues),
            issues_by_level=issues_by_level,
            issues_by_item=issues_by_item,
            issues_by_tag=issues_by_tag,
            issues=all_issues,
            processing_time_ms=sub_result.processing_time_ms + line_result.processing_time_ms + dup_result.processing_time_ms,
        )

        # Store per-analyser results
        self.validation_results["substation"] = sub_result
        self.validation_results["power_line"] = line_result
        self.validation_results["duplicates"] = dup_result
        self.validation_results["combined"] = combined
        self.last_validation = datetime.utcnow()

        # Update quality score
        self.quality_score.update_from_issues(combined)

        logger.info(f"Infrastructure validation found {combined.total_issues} issues")
        return combined

    async def validate_meter_alignment(
        self,
        meter_data: List[Dict[str, Any]],
        osm_data: Optional[Dict[str, Any]] = None,
    ) -> OsmoseValidationResult:
        """
        Validate meter alignment with infrastructure.

        Args:
            meter_data: List of meter dicts with meter_id, lat, lon
            osm_data: OSM data (if None, uses cached or fetched data)

        Returns:
            Validation result with alignment issues
        """
        logger.info(f"Running meter alignment validation for {len(meter_data)} meters")

        if not osm_data:
            osm_data = self._osm_data or await self._fetch_osm_data()

        # Initialize conflation analyser
        self._conflation_analyser = MeterConflation(
            country=self.config.country,
            config=self.config.conflation_config,
        )
        self._conflation_analyser.load_infrastructure(osm_data)

        result = self._conflation_analyser.run(meter_data)

        # Store result
        self.validation_results["meter_conflation"] = result

        # Update alignment score from match summary
        matches = []  # In production, the analyser would store these
        if len(meter_data) > 0:
            matched_count = meter_data  # placeholder
            penalty = min(50, result.total_issues * 2)
            self.quality_score.alignment_score = max(0, 100 - penalty)

        logger.info(f"Meter alignment validation found {result.total_issues} issues")
        return result
    
    def get_suggested_matches(self, meter_data: List[Dict[str, Any]],
                             osm_data: Optional[Dict[str, Any]] = None) -> List[MeterMatch]:
        """
        Get suggested meter-to-infrastructure matches.

        Args:
            meter_data: List of meter locations
            osm_data: OSM data (if None, uses cached)

        Returns:
            List of MeterMatch objects
        """
        logger.info("Calculating meter-to-infrastructure matches")

        if not osm_data:
            osm_data = self._osm_data
        if not osm_data:
            return []

        if not self._conflation_analyser:
            self._conflation_analyser = MeterConflation(
                country=self.config.country,
                config=self.config.conflation_config,
            )
            self._conflation_analyser.load_infrastructure(osm_data)

        # Run matching (returns result, but we need matches from analyser)
        self._conflation_analyser.run(meter_data)

        # Build match results from meter data
        matches = []
        for meter in meter_data:
            match = self._conflation_analyser._match_meter(meter)
            matches.append(match)

        logger.info(f"Found {sum(1 for m in matches if m.status == 'matched')} matches")
        return matches
    
    async def run_daily_analytics(self, target_date: Optional[date] = None) -> Optional[DailyAnalyticsResult]:
        """
        Run daily batch analytics.
        
        Args:
            target_date: Date to analyze (default: yesterday)
        
        Returns:
            Daily analytics result (or None if batch analytics not configured)
        """
        if not self.batch_analytics:
            logger.warning("Batch analytics not configured (no db_url)")
            return None
        
        return await self.batch_analytics.run_daily_analytics(target_date)
    
    def get_quality_score(self) -> Dict[str, float]:
        """Get current quality score"""
        return self.quality_score.to_dict()
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get comprehensive quality summary"""
        combined = self.validation_results.get("combined")
        return {
            'quality_score': self.get_quality_score(),
            'last_validation': self.last_validation.isoformat() if self.last_validation else None,
            'total_validations': len(self.validation_results),
            'total_issues': combined.total_issues if combined else 0,
            'analyser_results': {
                name: result.total_issues
                for name, result in self.validation_results.items()
            },
            'recent_issues': self._get_recent_issues(count=10),
        }

    def _get_recent_issues(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get most recent issues from combined result"""
        combined = self.validation_results.get("combined")
        if not combined:
            return []

        return [i.model_dump() for i in combined.issues[:count]]
    
    async def _fetch_osm_data(self) -> Dict[str, Any]:
        """
        Fetch OSM data for validation area.
        
        This is a placeholder - actual implementation would:
        1. Query Overpass API
        2. Load from local PBF file
        3. Query local PostgreSQL/PostGIS database
        """
        # TODO: Implement actual OSM data fetching
        logger.debug("Fetching OSM data (placeholder)")
        
        # Return empty structure for now
        return {
            'nodes': [],
            'ways': [],
            'relations': []
        }
    
    def _extract_power_poles(self, osm_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract power poles from OSM data"""
        poles = []
        for node in osm_data.get('nodes', []):
            tags = node.get('tags', {})
            if tags.get('power') in ['pole', 'tower']:
                poles.append({
                    'id': node.get('id'),
                    'lat': node.get('lat'),
                    'lon': node.get('lon'),
                    'tags': tags
                })
        return poles

    def _extract_power_lines(self, osm_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract power line features from OSM data."""
        lines = []
        for way in osm_data.get('ways', []):
            tags = way.get('tags', {})
            if tags.get('power') in ('line', 'cable', 'minor_line'):
                nodes = way.get('nodes', [])
                # Build coordinate list from node refs (simplified)
                coords = []
                for n in osm_data.get('nodes', []):
                    if n.get('id') in nodes:
                        coords.append([n.get('lon'), n.get('lat')])
                lines.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coords,
                    },
                    'properties': tags,
                })
        return lines


class GridQualityMonitor:
    """
    Real-time grid quality monitoring.
    
    Monitors simulation in real-time and flags quality issues:
    - Meter readings outside normal ranges
    - Infrastructure mismatches
    - Spatial inconsistencies
    """
    
    def __init__(self, quality_manager: GridQualityManager):
        """
        Initialize quality monitor.
        
        Args:
            quality_manager: Grid quality manager instance
        """
        self.quality_manager = quality_manager
        self.monitoring = False
        self.issues_detected: List[Dict[str, Any]] = []
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        self.monitoring = True
        logger.info("Grid quality monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring = False
        logger.info("Grid quality monitoring stopped")
    
    def validate_reading(self, reading: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate a single meter reading.
        
        Args:
            reading: Meter reading dictionary
        
        Returns:
            Issue dictionary if problem detected, None otherwise
        """
        if not self.monitoring:
            return None
        
        issues = []
        
        # Check voltage range
        voltage = reading.get('voltage_v', 230)
        if voltage < 207 or voltage > 253:  # ±10%
            issues.append({
                'type': 'voltage_out_of_range',
                'severity': 'high' if voltage < 200 or voltage > 260 else 'medium',
                'value': voltage,
                'expected': '207-253V',
                'meter_id': reading.get('meter_id'),
                'timestamp': reading.get('timestamp')
            })
        
        # Check frequency range
        frequency = reading.get('frequency_hz', 50)
        if frequency < 49.5 or frequency > 50.5:  # ±1%
            issues.append({
                'type': 'frequency_out_of_range',
                'severity': 'critical' if frequency < 49 or frequency > 51 else 'high',
                'value': frequency,
                'expected': '49.5-50.5Hz',
                'meter_id': reading.get('meter_id'),
                'timestamp': reading.get('timestamp')
            })
        
        # Check for negative values
        for field in ['energy_generated_kwh', 'energy_consumed_kwh']:
            value = reading.get(field, 0)
            if value < 0:
                issues.append({
                    'type': 'negative_value',
                    'severity': 'medium',
                    'field': field,
                    'value': value,
                    'meter_id': reading.get('meter_id'),
                    'timestamp': reading.get('timestamp')
                })
        
        # Store issues
        self.issues_detected.extend(issues)
        
        if issues:
            logger.warning(f"Quality issues detected in reading: {len(issues)} issues")
        
        return issues[0] if issues else None
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        return {
            'monitoring_active': self.monitoring,
            'total_issues_detected': len(self.issues_detected),
            'issues_by_type': self._count_issues_by_type(),
            'recent_issues': self.issues_detected[-10:]
        }
    
    def _count_issues_by_type(self) -> Dict[str, int]:
        """Count issues by type"""
        counts = {}
        for issue in self.issues_detected:
            issue_type = issue.get('type', 'unknown')
            counts[issue_type] = counts.get(issue_type, 0) + 1
        return counts


def create_quality_manager(db_url: Optional[str] = None) -> GridQualityManager:
    """
    Factory function to create grid quality manager.

    Args:
        db_url: Optional database URL for batch analytics

    Returns:
        Configured GridQualityManager instance
    """
    config = GridQualityConfig(
        conflation_distance_m=50.0,
        max_pole_distance_m=50.0,
        suspicious_distance_m=200.0,
    )

    return GridQualityManager(config=config, db_url=db_url)

