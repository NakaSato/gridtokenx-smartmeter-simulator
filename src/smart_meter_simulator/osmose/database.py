"""
OSMOSE Database Integration

PostgreSQL/PostGIS storage for OSMOSE validation results.
Supports efficient spatial queries for vector tile generation.
"""

import asyncpg
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .core.issue import OsmoseIssue, OsmoseValidationResult

logger = logging.getLogger(__name__)


class OSMOSEDatabase:
    """
    PostgreSQL database for OSMOSE data.
    
    Stores:
    - OSM data (from Osmosis import)
    - Validation results
    - Analyser history
    - Issue statistics
    """
    
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.conn_string,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")
    
    async def init_schema(self):
        """Initialize database schema"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            # Create issues table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS osmose_issues (
                    id SERIAL PRIMARY KEY,
                    issue_id INTEGER NOT NULL,
                    item INTEGER NOT NULL,
                    level INTEGER NOT NULL,
                    tags TEXT[] NOT NULL,
                    title TEXT NOT NULL,
                    detail TEXT,
                    fix TEXT,
                    osm_type VARCHAR(20),
                    osm_id BIGINT,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    subclass INTEGER,
                    text TEXT,
                    fix_suggestions JSONB,
                    analyser VARCHAR(100),
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    country VARCHAR(10)
                );
            """)
            
            # Create spatial index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_osmose_issues_geom 
                ON osmose_issues USING GIST (
                    ST_SetSRID(ST_MakePoint(lon, lat), 4326)
                );
            """)
            
            # Create analyser index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_osmose_issues_analyser
                ON osmose_issues(analyser);
            """)
            
            # Create level index
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_osmose_issues_level
                ON osmose_issues(level);
            """)
            
            logger.info("Database schema initialized")
    
    async def store_result(self, result: OsmoseValidationResult):
        """Store validation result in database"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            # Insert issues
            for issue in result.issues:
                await conn.execute("""
                    INSERT INTO osmose_issues (
                        issue_id, item, level, tags, title, detail, fix,
                        osm_type, osm_id, lat, lon, subclass, text,
                        fix_suggestions, analyser, timestamp, country
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    ON CONFLICT DO NOTHING
                """,
                    issue.id,
                    issue.item,
                    issue.level,
                    issue.tags,
                    issue.title,
                    issue.detail,
                    issue.fix,
                    issue.osm_type,
                    issue.osm_id,
                    issue.lat,
                    issue.lon,
                    issue.subclass,
                    issue.text,
                    json.dumps(issue.fix_suggestions) if issue.fix_suggestions else None,
                    issue.analyser,
                    datetime.fromisoformat(result.timestamp.replace("Z", "+00:00")) if result.timestamp else datetime.utcnow(),
                    result.country,
                )
        
        logger.info(f"Stored {result.total_issues} issues from {result.analyser}")
    
    async def get_issues(self, bbox: Optional[Dict[str, float]] = None,
                        level_min: int = 1, level_max: int = 3,
                        analyser: Optional[str] = None,
                        limit: int = 1000) -> List[OsmoseIssue]:
        """
        Query issues with filters.
        
        Args:
            bbox: Bounding box {north, south, east, west}
            level_min: Minimum severity level
            level_max: Maximum severity level
            analyser: Filter by analyser
            limit: Maximum results
            
        Returns:
            List of issues
        """
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            # Build query
            query = """
                SELECT * FROM osmose_issues
                WHERE level >= $1 AND level <= $2
            """
            params = [level_min, level_max]
            param_count = 2
            
            if bbox:
                param_count += 4
                query += f"""
                    AND lon >= ${param_count - 3}
                    AND lon <= ${param_count - 2}
                    AND lat >= ${param_count - 1}
                    AND lat <= ${param_count}
                """
                params.extend([bbox["west"], bbox["east"], bbox["south"], bbox["north"]])
            
            if analyser:
                param_count += 1
                query += f" AND analyser = ${param_count}"
                params.append(analyser)
            
            query += f" LIMIT ${param_count + 1}"
            params.append(limit)
            
            rows = await conn.fetch(query, *params)
            
            return [self._row_to_issue(row) for row in rows]
    
    async def get_statistics(self, country: Optional[str] = None) -> Dict[str, Any]:
        """Get validation statistics"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            # Total issues
            total = await conn.fetchval("SELECT COUNT(*) FROM osmose_issues")
            
            # Issues by level
            by_level = await conn.fetch("""
                SELECT level, COUNT(*) as count 
                FROM osmose_issues 
                GROUP BY level 
                ORDER BY level
            """)
            
            # Issues by analyser
            by_analyser = await conn.fetch("""
                SELECT analyser, COUNT(*) as count 
                FROM osmose_issues 
                GROUP BY analyser 
                ORDER BY count DESC
            """)
            
            # Issues by item
            by_item = await conn.fetch("""
                SELECT item, COUNT(*) as count 
                FROM osmose_issues 
                GROUP BY item 
                ORDER BY count DESC
                LIMIT 20
            """)
            
            return {
                "total_issues": total or 0,
                "issues_by_level": {str(row["level"]): row["count"] for row in by_level},
                "issues_by_analyser": {row["analyser"]: row["count"] for row in by_analyser},
                "issues_by_item": {str(row["item"]): row["count"] for row in by_item},
                "country": country,
            }
    
    async def clear_issues(self, analyser: Optional[str] = None):
        """Clear issues (optionally by analyser)"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            if analyser:
                await conn.execute("DELETE FROM osmose_issues WHERE analyser = $1", analyser)
            else:
                await conn.execute("TRUNCATE osmose_issues")
        
        logger.info(f"Cleared issues (analyser: {analyser})")
    
    def _row_to_issue(self, row) -> OsmoseIssue:
        """Convert database row to OsmoseIssue"""
        return OsmoseIssue(
            id=row["issue_id"],
            item=row["item"],
            level=row["level"],
            tags=row["tags"],
            title=row["title"],
            detail=row["detail"],
            fix=row["fix"],
            osm_type=row["osm_type"],
            osm_id=row["osm_id"],
            lat=row["lat"],
            lon=row["lon"],
            subclass=row["subclass"],
            text=row["text"],
            fix_suggestions=row["fix_suggestions"],
            analyser=row["analyser"],
            timestamp=row["timestamp"].isoformat() if row["timestamp"] else None,
        )
