import geojson
import geopandas as gpd
from os.path import basename
from area import area

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

def ROI_area(ROI_filename: str, working_directory: str = ".") -> float:
    try:
        ROI_gpd = gpd.read_file(ROI_filename).to_crs(WGS84)
        ROI_acre = ROI_gpd.iloc[0]['Acres']
    
    except KeyError:

        ROI_gpd = gpd.read_file(ROI_filename).to_crs(WGS84)
        filename = basename(ROI_filename)
        expt = ROI_gpd.to_file(filename, driver="GeoJSON")
        impt = open(filename)
        ROI_base = geojson.load(impt)
        ROI_geom = ROI_base['features'][0]['geometry']
        ROI_acre = area(ROI_geom) * 0.000247105
    
    return (ROI_acre)
