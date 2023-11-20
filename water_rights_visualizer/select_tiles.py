from typing import List
from os.path import join, abspath, dirname
import geopandas as gpd
from shapely.geometry import Polygon

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01

def select_tiles(target_geometry_latlon: Polygon) -> List[str]:
    tiles_df = gpd.read_file(join(abspath(dirname(__file__)), "ARD_tiles.geojson")).to_crs(WGS84)
    selection = tiles_df.intersects(target_geometry_latlon.buffer(TILE_SELECTION_BUFFER_RADIUS_DEGREES))
    selected_tiles_df = tiles_df[selection]
    tiles = [item[2:] for item in list(selected_tiles_df["name"])]
    
    return tiles
