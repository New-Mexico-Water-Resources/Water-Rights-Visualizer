from typing import List
import geopandas as gpd
import rasterio
from affine import Affine
from os.path import exists, join, basename, splitext
from glob import glob
from logging import getLogger
import numpy as np
from shapely.geometry import Point, Polygon
from rasterio.warp import reproject
from rasterio.windows import Window, transform as window_transform

from .select_tiles import select_tiles
from .read_subset import read_subset

logger = getLogger(__name__)

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
UTM = "+proj=utm +zone=13 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
BUFFER_METERS = 2000
CELL_SIZE_DEGREES = 0.0003
CELL_SIZE_METERS = 30
TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01

def generate_subset(
        raster_directory: str,
        ROI_latlon: Polygon,
        ROI_acres: float,
        variable_name: str,
        subset_filename: str,
        cell_size: float = None,
        buffer_size: float = None,
        target_CRS: str = None) -> (np.ndarray, Affine):
    """
    This function generates a subset of a raster based on a region of interest (ROI).
    
    Parameters:
    raster_directory (str): The directory where the raster files are located.
    ROI_latlon (Polygon): The region of interest in latitude and longitude coordinates.
    ROI_acres (float): The size of the region of interest in acres.
    variable_name (str): The name of the variable to be subsetted.
    subset_filename (str): The filename for the output subset.
    cell_size (float, optional): The cell size for the output raster. Defaults to None.
    buffer_size (float, optional): The buffer size for the output raster. Defaults to None.
    target_CRS (str, optional): The coordinate reference system for the output raster. Defaults to None.

    Returns:
    np.ndarray: The subsetted raster.
    Affine: The affine transformation for the subsetted raster.
    """

    logger.info(f"generating {variable_name} subset")

    roi_size = round(ROI_acres, 2)        

    if roi_size <= 4:
        BUFFER_DEGREES = 0.005
    elif 4 < roi_size <= 10:
        BUFFER_DEGREES = 0.005
    elif 10 < roi_size <= 30:
        roi_filter = roi_size / 4
        BUFFER_DEGREES = roi_filter / 1000
    elif 30 < roi_size <= 60:
        roi_filter = roi_size / 6
        BUFFER_DEGREES = roi_filter / 1000
    else: 
        roi_filter = roi_size / 8
        BUFFER_DEGREES = roi_filter / 1000
    
    if cell_size is None:
        cell_size = CELL_SIZE_DEGREES

    if buffer_size is None:
        buffer_size = BUFFER_DEGREES

    if target_CRS is None:
        target_CRS = WGS84

    if exists(subset_filename):
        logger.info(f"loading existing {variable_name} subset file: {subset_filename}")

        with rasterio.open(subset_filename, "r") as f:
            subset = f.read(1)
            affine = f.transform

        return subset, affine
    
    logger.info(f"generating {variable_name} subset")

    tiles = select_tiles(ROI_latlon)
    logger.info(f"tiles: {tiles}")
    ROI_projected = gpd.GeoDataFrame({}, geometry=[ROI_latlon], crs=WGS84).to_crs(target_CRS).geometry[0]
    centroid = ROI_projected.centroid
    x_min = centroid.x - buffer_size
    x_max = centroid.x + buffer_size
    y_min = centroid.y - buffer_size
    y_max = centroid.y + buffer_size

    target_affine = Affine(
        cell_size,
        0,
        x_min,
        0,
        -cell_size,
        y_max
    )

    width_meters = x_max - x_min
    target_cols = int(width_meters / cell_size)
    height_meters = (y_max - y_min) 
    target_rows = int(height_meters / cell_size)
    output_raster = np.full((target_rows, target_cols), np.nan, dtype=np.float32)
    
    for tile in tiles:
        pattern = join(raster_directory, "**", f"*_{tile}_*_{variable_name}.tif")
        logger.info(f"searching pattern: {pattern}")
        matches = sorted(glob(pattern, recursive=True))
        
        if len(matches) == 0:
            logger.info(f"no files found for tile: {tile}")
            files_found = sorted(glob(join(raster_directory, '**', '*'), recursive=True))
            tiles_found = sorted(set([splitext(basename(filename))[0].split("_")[2] for filename in files_found]))
            logger.info(f"files found: {', '.join(tiles_found)}")
            continue
        
        input_filename = matches[0]
        logger.info(f"{tile}: {input_filename}")

        source_subset, source_affine, source_CRS = read_subset(input_filename, x_min, y_min, x_max, y_max, target_CRS)

        target_surface = np.full((target_rows, target_cols), np.nan, dtype=np.float32)

        reproject(
            source_subset,
            target_surface,
            src_transform=source_affine,
            src_crs=source_CRS,
            src_nodata=np.nan,
            dst_transform=target_affine,
            dst_crs=target_CRS,
            dst_nodata=np.nan
        )
        
        output_raster = np.where(np.isnan(output_raster), target_surface, output_raster)
    if np.all(np.isnan(output_raster)):
        raise ValueError("blank output raster")
    
    if not exists(subset_filename):
        subset_profile = {
            "driver": "GTiff",
            "compress": "LZW",
            "dtype": np.float32,
            "transform": target_affine,
            "crs": target_CRS,
            "width": target_cols,
            "height": target_rows,
            "count": 1
        }
    
        logger.info("writing subset: {}".format(subset_filename))
        with rasterio.open(subset_filename, "w", **subset_profile) as input_file:
            input_file.write(output_raster.astype(np.float32), 1)

    return output_raster, target_affine
