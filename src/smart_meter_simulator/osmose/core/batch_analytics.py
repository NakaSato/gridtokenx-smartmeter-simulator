"""
Batch Analytics Pipeline for Smart Meter Simulator

Inspired by Osmose batch processing patterns (osmose_run.py).
Provides offline analytics for historical grid data including:
- Daily/weekly/monthly grid performance analysis
- Locational Marginal Pricing (LMP) calculations
- Anomaly detection
- Report generation

Usage:
    from smart_meter_simulator.osmose.batch_analytics import BatchAnalyticsPipeline
    
    pipeline = BatchAnalyticsPipeline(db_url="postgresql://...")
    
    # Run daily analytics
    results = await pipeline.run_daily_analytics(date="2024-03-30")
    
    # Generate monthly report
    report = await pipeline.generate_monthly_report(year=2024, month=3)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, date
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AnalyticsType(Enum):
    """Types of analytics jobs"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class AnalyticsJob:
    """Represents an analytics job"""
    
    job_id: str
    job_type: AnalyticsType
    start_date: datetime
    end_date: datetime
    status: str = "pending"  # pending, running, completed, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class DailyAnalyticsResult:
    """Results from daily analytics run"""
    
    date: date
    total_readings: int
    total_generation_kwh: float
    total_consumption_kwh: float
    total_battery_kwh: float
    avg_voltage: float
    avg_frequency: float
    peak_demand_kw: float
    peak_generation_kw: float
    lmp_by_node: Dict[str, float]  # Locational Marginal Prices
    anomalies_detected: int
    grid_stability_score: float  # 0-100
    market_clearing_price: float
    total_trades: int
    vpp_dispatch_events: int
    frequency_regulation_events: int


@dataclass
class AnomalyReport:
    """Detected anomaly in grid data"""
    
    anomaly_id: str
    timestamp: datetime
    meter_id: str
    anomaly_type: str  # voltage_spike, frequency_deviation, consumption_anomaly, etc.
    severity: str  # low, medium, high, critical
    value: float
    expected_value: float
    deviation_percent: float
    description: str
    recommended_action: str


class BatchAnalyticsPipeline:
    """
    Batch processing pipeline for grid analytics.
    
    Inspired by Osmose's batch processing pattern:
    1. Load historical data
    2. Run analytics engines
    3. Calculate metrics
    4. Detect anomalies
    5. Generate reports
    6. Store results
    """
    
    def __init__(self, db_url: Optional[str] = None, 
                 influxdb_url: Optional[str] = None):
        """
        Initialize batch analytics pipeline.
        
        Args:
            db_url: PostgreSQL database URL
            influxdb_url: InfluxDB URL for time-series data
        """
        self.db_url = db_url
        self.influxdb_url = influxdb_url
        self.jobs: List[AnalyticsJob] = []
        self.current_job: Optional[AnalyticsJob] = None
        
        # Analytics engines (initialized on first run)
        self._lmp_calculator = None
        self._anomaly_detector = None
        self._stability_analyzer = None
    
    async def run_daily_analytics(self, target_date: Optional[date] = None) -> DailyAnalyticsResult:
        """
        Run daily analytics pipeline.
        
        Args:
            target_date: Date to analyze (default: yesterday)
        
        Returns:
            Daily analytics result
        """
        if target_date is None:
            target_date = datetime.utcnow().date() - timedelta(days=1)
        
        logger.info(f"Starting daily analytics for {target_date}")
        
        # Create job
        job = AnalyticsJob(
            job_id=f"daily_{target_date.isoformat()}",
            job_type=AnalyticsType.DAILY,
            start_date=datetime.combine(target_date, datetime.min.time()),
            end_date=datetime.combine(target_date, datetime.max.time())
        )
        self.jobs.append(job)
        self.current_job = job
        
        try:
            job.status = "running"
            
            # Step 1: Load historical meter readings
            logger.info("Step 1: Loading meter readings")
            readings = await self._load_meter_readings(job.start_date, job.end_date)
            
            # Step 2: Calculate aggregate metrics
            logger.info("Step 2: Calculating aggregate metrics")
            metrics = self._calculate_aggregate_metrics(readings)
            
            # Step 3: Calculate Locational Marginal Prices
            logger.info("Step 3: Calculating LMP")
            lmp_by_node = await self._calculate_lmp(readings, job.start_date)
            
            # Step 4: Detect anomalies
            logger.info("Step 4: Detecting anomalies")
            anomalies = await self._detect_anomalies(readings)
            
            # Step 5: Calculate grid stability
            logger.info("Step 5: Analyzing grid stability")
            stability_score = self._calculate_stability_score(readings, anomalies)
            
            # Step 6: Market analysis
            logger.info("Step 6: Analyzing market dynamics")
            market_metrics = await self._analyze_market(job.start_date, job.end_date)
            
            # Compile results
            result = DailyAnalyticsResult(
                date=target_date,
                total_readings=metrics['total_readings'],
                total_generation_kwh=metrics['total_generation_kwh'],
                total_consumption_kwh=metrics['total_consumption_kwh'],
                total_battery_kwh=metrics['total_battery_kwh'],
                avg_voltage=metrics['avg_voltage'],
                avg_frequency=metrics['avg_frequency'],
                peak_demand_kw=metrics['peak_demand_kw'],
                peak_generation_kw=metrics['peak_generation_kw'],
                lmp_by_node=lmp_by_node,
                anomalies_detected=len(anomalies),
                grid_stability_score=stability_score,
                market_clearing_price=market_metrics.get('clearing_price', 0.0),
                total_trades=market_metrics.get('total_trades', 0),
                vpp_dispatch_events=market_metrics.get('vpp_events', 0),
                frequency_regulation_events=market_metrics.get('frequency_events', 0)
            )
            
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.results = {
                'metrics': metrics,
                'lmp': lmp_by_node,
                'anomalies': [a.__dict__ for a in anomalies],
                'stability_score': stability_score,
                'market': market_metrics
            }
            
            logger.info(f"Daily analytics completed: {result.total_readings} readings, "
                       f"{result.anomalies_detected} anomalies, "
                       f"stability score: {result.grid_stability_score:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Daily analytics failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            raise
    
    async def run_weekly_analytics(self, week_start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Run weekly analytics by aggregating daily results.
        
        Args:
            week_start_date: Monday of the week to analyze
        
        Returns:
            Weekly analytics summary
        """
        if week_start_date is None:
            # Get last Monday
            today = datetime.utcnow().date()
            week_start_date = today - timedelta(days=today.weekday()) - timedelta(weeks=1)
        
        logger.info(f"Starting weekly analytics for week of {week_start_date}")
        
        # Aggregate daily results
        daily_results = []
        for i in range(7):
            current_date = week_start_date + timedelta(days=i)
            try:
                daily_result = await self.run_daily_analytics(current_date)
                daily_results.append(daily_result)
            except Exception as e:
                logger.warning(f"Failed to analyze {current_date}: {e}")
        
        if not daily_results:
            raise ValueError("No daily results available for weekly aggregation")
        
        # Aggregate metrics
        weekly_summary = {
            'week_start': week_start_date.isoformat(),
            'week_end': (week_start_date + timedelta(days=6)).isoformat(),
            'total_readings': sum(r.total_readings for r in daily_results),
            'total_generation_kwh': sum(r.total_generation_kwh for r in daily_results),
            'total_consumption_kwh': sum(r.total_consumption_kwh for r in daily_results),
            'avg_voltage': sum(r.avg_voltage for r in daily_results) / len(daily_results),
            'avg_frequency': sum(r.avg_frequency for r in daily_results) / len(daily_results),
            'avg_stability_score': sum(r.grid_stability_score for r in daily_results) / len(daily_results),
            'total_anomalies': sum(r.anomalies_detected for r in daily_results),
            'total_trades': sum(r.total_trades for r in daily_results),
            'avg_lmp_by_node': self._average_lmp_by_node([r.lmp_by_node for r in daily_results]),
            'daily_breakdown': [
                {
                    'date': r.date.isoformat(),
                    'generation_kwh': r.total_generation_kwh,
                    'consumption_kwh': r.total_consumption_kwh,
                    'stability_score': r.grid_stability_score,
                    'anomalies': r.anomalies_detected
                }
                for r in daily_results
            ]
        }
        
        logger.info(f"Weekly analytics completed: {weekly_summary['total_readings']} total readings")
        return weekly_summary
    
    async def generate_monthly_report(self, year: int, month: int) -> Dict[str, Any]:
        """
        Generate comprehensive monthly report.
        
        Args:
            year: Year
            month: Month (1-12)
        
        Returns:
            Monthly report dictionary
        """
        logger.info(f"Generating monthly report for {year}-{month:02d}")
        
        # Get all weeks in month
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # Aggregate weekly results
        weekly_results = []
        current_date = month_start
        
        while current_date <= month_end:
            # Find Monday of this week
            week_start = current_date - timedelta(days=current_date.weekday())
            try:
                weekly_result = await self.run_weekly_analytics(week_start)
                weekly_results.append(weekly_result)
            except Exception as e:
                logger.warning(f"Failed to analyze week of {week_start}: {e}")
            
            # Move to next week
            current_date = week_start + timedelta(weeks=1)
        
        # Compile monthly report
        monthly_report = {
            'year': year,
            'month': month,
            'period': f"{month_start.isoformat()} to {month_end.isoformat()}",
            'total_readings': sum(w['total_readings'] for w in weekly_results),
            'total_generation_kwh': sum(w['total_generation_kwh'] for w in weekly_results),
            'total_consumption_kwh': sum(w['total_consumption_kwh'] for w in weekly_results),
            'net_energy_kwh': sum(w['total_generation_kwh'] for w in weekly_results) - 
                             sum(w['total_consumption_kwh'] for w in weekly_results),
            'avg_voltage': sum(w['avg_voltage'] for w in weekly_results) / len(weekly_results),
            'avg_frequency': sum(w['avg_frequency'] for w in weekly_results) / len(weekly_results),
            'avg_stability_score': sum(w['avg_stability_score'] for w in weekly_results) / len(weekly_results),
            'total_anomalies': sum(w['total_anomalies'] for w in weekly_results),
            'total_trades': sum(w['total_trades'] for w in weekly_results),
            'avg_lmp': sum(w['avg_lmp_by_node'].get('average', 0) for w in weekly_results) / len(weekly_results),
            'weekly_breakdown': weekly_results,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Add trends analysis
        monthly_report['trends'] = self._analyze_trends(weekly_results)
        
        logger.info(f"Monthly report generated: {monthly_report['total_readings']} readings")
        return monthly_report
    
    async def _load_meter_readings(self, start_date: datetime, 
                                   end_date: datetime) -> List[Dict[str, Any]]:
        """
        Load meter readings from database.
        
        This is a placeholder - actual implementation would query
        PostgreSQL or InfluxDB based on configuration.
        """
        # TODO: Implement actual database query
        # Example: query InfluxDB for time-series data
        # Example: query PostgreSQL for aggregated data
        
        logger.debug(f"Loading readings from {start_date} to {end_date}")
        
        # Placeholder - return empty list
        return []
    
    def _calculate_aggregate_metrics(self, readings: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate metrics from readings"""
        
        if not readings:
            return {
                'total_readings': 0,
                'total_generation_kwh': 0.0,
                'total_consumption_kwh': 0.0,
                'total_battery_kwh': 0.0,
                'avg_voltage': 230.0,
                'avg_frequency': 50.0,
                'peak_demand_kw': 0.0,
                'peak_generation_kw': 0.0
            }
        
        total_gen = sum(r.get('energy_generated_kwh', 0) for r in readings)
        total_cons = sum(r.get('energy_consumed_kwh', 0) for r in readings)
        total_batt = sum(r.get('battery_level_kwh', 0) for r in readings)
        
        voltages = [r.get('voltage_v', 230) for r in readings]
        frequencies = [r.get('frequency_hz', 50) for r in readings]
        powers = [r.get('energy_consumed_kwh', 0) for r in readings]
        
        return {
            'total_readings': len(readings),
            'total_generation_kwh': total_gen,
            'total_consumption_kwh': total_cons,
            'total_battery_kwh': total_batt,
            'avg_voltage': sum(voltages) / len(voltages) if voltages else 230.0,
            'avg_frequency': sum(frequencies) / len(frequencies) if frequencies else 50.0,
            'peak_demand_kw': max(powers) if powers else 0.0,
            'peak_generation_kw': max(r.get('energy_generated_kwh', 0) for r in readings)
        }
    
    async def _calculate_lmp(self, readings: List[Dict[str, Any]], 
                            date: datetime) -> Dict[str, float]:
        """
        Calculate Locational Marginal Prices by node.
        
        LMP components:
        1. Energy component (generation cost)
        2. Congestion component (transmission constraints)
        3. Loss component (transmission losses)
        """
        # TODO: Implement actual LMP calculation
        # This would integrate with the market engine
        
        logger.debug(f"Calculating LMP for {date}")
        
        # Placeholder - return sample LMP values
        return {
            'node_001': 2.5,
            'node_002': 2.6,
            'node_003': 2.4,
            'average': 2.5
        }
    
    async def _detect_anomalies(self, readings: List[Dict[str, Any]]) -> List[AnomalyReport]:
        """
        Detect anomalies in meter readings.
        
        Anomaly types:
        - Voltage spikes/sags
        - Frequency deviations
        - Consumption anomalies (potential fraud)
        - Communication failures
        """
        anomalies = []
        
        if not readings:
            return anomalies
        
        for reading in readings:
            # Check voltage anomalies
            voltage = reading.get('voltage_v', 230)
            if voltage < 207 or voltage > 253:  # ±10% tolerance
                anomalies.append(AnomalyReport(
                    anomaly_id=f"volt_{reading.get('meter_id')}_{reading.get('timestamp')}",
                    timestamp=reading.get('timestamp'),
                    meter_id=reading.get('meter_id'),
                    anomaly_type='voltage_deviation',
                    severity='high' if voltage < 200 or voltage > 260 else 'medium',
                    value=voltage,
                    expected_value=230,
                    deviation_percent=abs(voltage - 230) / 230 * 100,
                    description=f"Voltage {voltage}V outside normal range",
                    recommended_action='Inspect meter and local grid connection'
                ))
            
            # Check frequency anomalies
            frequency = reading.get('frequency_hz', 50)
            if frequency < 49.5 or frequency > 50.5:  # ±1% tolerance
                anomalies.append(AnomalyReport(
                    anomaly_id=f"freq_{reading.get('meter_id')}_{reading.get('timestamp')}",
                    timestamp=reading.get('timestamp'),
                    meter_id=reading.get('meter_id'),
                    anomaly_type='frequency_deviation',
                    severity='critical' if frequency < 49 or frequency > 51 else 'high',
                    value=frequency,
                    expected_value=50,
                    deviation_percent=abs(frequency - 50) / 50 * 100,
                    description=f"Frequency {frequency}Hz outside normal range",
                    recommended_action='Check grid frequency regulation'
                ))
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        return anomalies
    
    def _calculate_stability_score(self, readings: List[Dict[str, Any]], 
                                   anomalies: List[AnomalyReport]) -> float:
        """
        Calculate grid stability score (0-100).
        
        Factors:
        - Voltage stability (40%)
        - Frequency stability (40%)
        - Anomaly rate (20%)
        """
        if not readings:
            return 100.0
        
        # Voltage stability
        voltages = [r.get('voltage_v', 230) for r in readings]
        avg_voltage = sum(voltages) / len(voltages)
        voltage_std = (sum((v - avg_voltage) ** 2 for v in voltages) / len(voltages)) ** 0.5
        voltage_score = max(0, 100 - voltage_std * 2)  # Penalize high variance
        
        # Frequency stability
        frequencies = [r.get('frequency_hz', 50) for r in readings]
        avg_freq = sum(frequencies) / len(frequencies)
        freq_std = (sum((f - avg_freq) ** 2 for f in frequencies) / len(frequencies)) ** 0.5
        freq_score = max(0, 100 - freq_std * 100)  # Penalize high variance
        
        # Anomaly rate
        anomaly_rate = len(anomalies) / len(readings) * 100
        anomaly_score = max(0, 100 - anomaly_rate * 10)
        
        # Weighted average
        stability_score = (
            0.4 * voltage_score +
            0.4 * freq_score +
            0.2 * anomaly_score
        )
        
        return min(100, max(0, stability_score))
    
    async def _analyze_market(self, start_date: datetime, 
                             end_date: datetime) -> Dict[str, Any]:
        """Analyze market dynamics for period"""
        # TODO: Integrate with market engine
        return {
            'clearing_price': 2.5,
            'total_trades': 0,
            'vpp_events': 0,
            'frequency_events': 0
        }
    
    def _average_lmp_by_node(self, lmp_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Calculate average LMP across multiple days"""
        if not lmp_list:
            return {'average': 0.0}
        
        all_nodes = set()
        for lmp in lmp_list:
            all_nodes.update(lmp.keys())
        
        avg_lmp = {}
        for node in all_nodes:
            values = [lmp.get(node, 0) for lmp in lmp_list if node in lmp]
            if values:
                avg_lmp[node] = sum(values) / len(values)
        
        # Calculate overall average
        if avg_lmp:
            avg_lmp['average'] = sum(v for k, v in avg_lmp.items() if k != 'average') / len(avg_lmp)
        else:
            avg_lmp['average'] = 0.0
        
        return avg_lmp
    
    def _analyze_trends(self, weekly_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """Analyze trends from weekly data"""
        if len(weekly_results) < 2:
            return {'trend': 'insufficient_data'}
        
        # Analyze generation trend
        gen_values = [w['total_generation_kwh'] for w in weekly_results]
        if gen_values[-1] > gen_values[0] * 1.1:
            gen_trend = 'increasing'
        elif gen_values[-1] < gen_values[0] * 0.9:
            gen_trend = 'decreasing'
        else:
            gen_trend = 'stable'
        
        # Analyze stability trend
        stab_values = [w['avg_stability_score'] for w in weekly_results]
        if stab_values[-1] > stab_values[0] * 1.05:
            stab_trend = 'improving'
        elif stab_values[-1] < stab_values[0] * 0.95:
            stab_trend = 'degrading'
        else:
            stab_trend = 'stable'
        
        return {
            'generation_trend': gen_trend,
            'stability_trend': stab_trend,
            'weeks_analyzed': len(weekly_results)
        }
    
    def get_job_status(self, job_id: str) -> Optional[AnalyticsJob]:
        """Get status of a specific job"""
        for job in self.jobs:
            if job.job_id == job_id:
                return job
        return None
    
    def get_all_jobs(self) -> List[AnalyticsJob]:
        """Get all jobs"""
        return self.jobs


async def run_batch_analytics_demo():
    """Demo function showing batch analytics usage"""
    pipeline = BatchAnalyticsPipeline()
    
    # Run daily analytics
    print("Running daily analytics...")
    daily_result = await pipeline.run_daily_analytics()
    print(f"Daily result: {daily_result.total_readings} readings")
    
    # Run weekly analytics
    print("\nRunning weekly analytics...")
    weekly_result = await pipeline.run_weekly_analytics()
    print(f"Weekly result: {weekly_result['total_readings']} total readings")
    
    # Generate monthly report
    print("\nGenerating monthly report...")
    monthly_report = await pipeline.generate_monthly_report(2024, 3)
    print(f"Monthly report: {monthly_report['total_readings']} total readings")


if __name__ == "__main__":
    asyncio.run(run_batch_analytics_demo())
