from typing import List
from os.path import join, abspath, dirname
import geopandas as gpd
from shapely.geometry import Polygon

from .constants import WGS84
from .constants import TILE_SELECTION_BUFFER_RADIUS_DEGREES

def select_tiles(target_geometry_latlon: Polygon) -> List[str]:
    """
    Selects tiles based on the target geometry.

    Args:
        target_geometry_latlon (Polygon): The target geometry in latlon coordinates.

    Returns:
        List[str]: A list of selected tiles.
    """
    # Read the ARD tiles GeoJSON file and convert it to WGS84 coordinate system
    tiles_df = gpd.read_file(join(abspath(dirname(__file__)), "ARD_tiles.geojson")).to_crs(WGS84)
    
    # Perform tile selection based on the intersection with the target geometry buffer
    selection = tiles_df.intersects(target_geometry_latlon.buffer(TILE_SELECTION_BUFFER_RADIUS_DEGREES))
    selected_tiles_df = tiles_df[selection]
    
    # Extract the tile names from the selected tiles dataframe
    tiles = [item[2:] for item in list(selected_tiles_df["name"])]
    
    return tiles
