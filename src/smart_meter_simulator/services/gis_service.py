
import logging
import random
import os
import geopandas as gpd
from shapely.geometry import Point

logger = logging.getLogger(__name__)

class GISService:
    """
    Manages Geographical Information System (GIS) data for the simulator.
    Loads Thailand Shapefiles to provide real coordinates for Grid Nodes.
    """
    
    def __init__(self, shapefile_path: str = "gadm41_THA_shp/gadm41_THA_1.shp"):
        self.shapefile_path = shapefile_path
        self.gdf = None
        self._load_data()
        
    def _load_data(self):
        try:
            if os.path.exists(self.shapefile_path):
                logger.info(f"Loading Shapefile from {self.shapefile_path}...")
                self.gdf = gpd.read_file(self.shapefile_path)
                logger.info("Shapefile loaded successfully.")
            else:
                logger.warning(f"Shapefile not found at {self.shapefile_path}. GIS features disabled.")
        except Exception as e:
            logger.error(f"Failed to load shapefile: {e}")

    def get_random_point_in_province(self, province_name: str) -> tuple[float, float]:
        """
        Returns a random (lat, lon) within the specified province polygon.
        """
        if self.gdf is None:
            # Fallback: Center of Bangkok (fixed)
            return (13.7563, 100.5018)
            
        # Search for province (Case insensitive partial match)
        # GADM Column 'NAME_1' usually holds province names
        province = self.gdf[self.gdf['NAME_1'].str.contains(province_name, case=False, na=False)]
        
        if province.empty:
            logger.warning(f"Province '{province_name}' not found. Using Bangkok default.")
            province = self.gdf[self.gdf['NAME_1'] == "Bangkok"]
            
        if province.empty:
             # Fallback if even Bangkok fails
             return (13.7563, 100.5018)

        # Get Polygon
        poly = province.geometry.values[0]
        
        # Get Centroid
        centroid = poly.centroid
        return (centroid.y, centroid.x) # Lat, Lon
