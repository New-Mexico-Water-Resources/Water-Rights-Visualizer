from logging import getLogger
import numpy as np
from shapely.geometry import Point
import geopandas as gpd
from affine import Affine
import rasterio
from rasterio.windows import Window, transform as window_transform

logger = getLogger(__name__)

def read_subset(input_filename: str, x_min: float, y_min: float, x_max: float, y_max: float, target_CRS: str) -> (np.ndarray, Affine, str):        
    """
    This function reads a subset of a raster file that intersects with a given bounding box.
    
    Parameters:
    input_filename (str): The path to the input raster file.
    x_min, y_min, x_max, y_max (float): The coordinates of the bounding box in the target CRS.
    target_CRS (str): The Coordinate Reference System of the bounding box.
    
    Returns:
    source_subset (np.ndarray): The subset of the raster file that intersects with the bounding box.
    source_affine (Affine): The affine transformation of the subset.
    source_CRS (str): The Coordinate Reference System of the raster file.
    """
    # Open the raster file
    with rasterio.open(input_filename, "r") as input_file:
        # Get the CRS and affine transformation of the raster file
        source_CRS = input_file.crs
        input_affine = input_file.transform
        
        # Convert the coordinates of the bounding box to the source CRS and get the corresponding rows and columns
        ul = gpd.GeoDataFrame({}, geometry=[Point(x_min, y_max)], crs=target_CRS).to_crs(source_CRS).geometry[0]
        col_ul, row_ul = ~input_affine * (ul.x, ul.y)
        col_ul = int(col_ul)
        row_ul = int(row_ul)
        
        ur = gpd.GeoDataFrame({}, geometry=[Point(x_max, y_max)], crs=target_CRS).to_crs(source_CRS).geometry[0]
        col_ur, row_ur = ~input_affine * (ur.x, ur.y)
        col_ur = int(col_ur)
        row_ur = int(row_ur)
        
        lr = gpd.GeoDataFrame({}, geometry=[Point(x_max, y_min)], crs=target_CRS).to_crs(source_CRS).geometry[0]
        col_lr, row_lr = ~input_affine * (lr.x, lr.y)
        col_lr = int(col_lr)
        row_lr = int(row_lr)
        
        ll = gpd.GeoDataFrame({}, geometry=[Point(x_min, y_min)], crs=target_CRS).to_crs(source_CRS).geometry[0]
        col_ll, row_ll = ~input_affine * (ll.x, ll.y)
        col_ll = int(col_ll)
        row_ll = int(row_ll)
        
        # Get the minimum and maximum rows and columns
        col_min = min(col_ul, col_ll)
        col_min = max(col_min, 0)
        col_max = max(col_ur, col_lr)
        
        row_min = min(row_ul, row_ur)
        row_min = max(row_min, 0)
        row_max = max(row_ll, row_lr)
        
        # Define the window
        window = (row_min, row_max), (col_min, col_max)
        
        # Check if the raster file intersects with the bounding box
        if row_min < 0 or col_min < 0 or row_max <= row_min or col_max <= col_min:
            raise(f"raster does not intersect target surface: {input_filename}")

        # Read the subset from the raster file
        window = Window.from_slices(*window)
        source_subset = input_file.read(1, window=window)
        source_affine = window_transform(window, input_affine)
    
    return source_subset, source_affine, source_CRS
