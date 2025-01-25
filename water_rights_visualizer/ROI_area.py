import geojson
import geopandas as gpd
from os.path import basename
from area import area

from .constants import WGS84


def ROI_area(ROI_filename: str, working_directory: str = ".") -> float:
    ROI_gpd = gpd.read_file(ROI_filename).to_crs(WGS84)

    # Use pre-calculated "Acres" column if available
    if "Acres" in ROI_gpd.columns:
        return ROI_gpd.iloc[0]["Acres"]

    # Calculate area manually if "Acres" is unavailable
    filename = basename(ROI_filename)
    ROI_gpd.to_file(filename, driver="GeoJSON")
    with open(filename) as f:
        ROI_geom = geojson.load(f)["features"][0]["geometry"]
    return area(ROI_geom) * 0.000247105
