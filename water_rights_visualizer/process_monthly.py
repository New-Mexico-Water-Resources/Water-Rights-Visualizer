import logging
from os import makedirs
from os.path import join, exists
from datetime import datetime, timedelta
import numpy as np
from shapely.geometry import Polygon
import pandas as pd
from affine import Affine
import rasterio
from rasterio.features import geometry_mask
from dateutil.relativedelta import relativedelta

import raster as rt

from .constants import START_MONTH, END_MONTH

logger = logging.getLogger(__name__)

def process_monthly(
        ET_stack: np.ndarray,
        PET_stack: np.ndarray,
        ROI_latlon: Polygon,
        ROI_name: str,
        subset_affine: Affine,
        CRS: str,
        year: int,
        monthly_sums_directory: str,
        monthly_means_directory: str,
        start_month: int = START_MONTH,
        end_month: int = END_MONTH) -> pd.DataFrame:
    """
    Process monthly values for a given year and generate monthly means.

    Args:
        ET_stack (np.ndarray): Array of ET values for each day of the year.
        PET_stack (np.ndarray): Array of PET values for each day of the year.
        ROI_latlon (Polygon): Polygon representing the region of interest.
        ROI_name (str): Name of the region of interest.
        subset_affine (Affine): Affine transformation for the subset.
        CRS (str): Coordinate reference system.
        year (int): Year for which to process the monthly values.
        monthly_sums_directory (str): Directory to store monthly sum files.
        monthly_means_directory (str): Directory to store monthly means files.

    Returns:
        pd.DataFrame: DataFrame containing the monthly means.
    """
    logger.info("generating monthly means")
    monthly_means_filename = join(monthly_means_directory, f"{year}_monthly_means.csv")
    
    if exists(monthly_means_filename):
        logger.info(f"loading monthly means: {monthly_means_filename}")
        monthly_means_df = pd.read_csv(monthly_means_filename)
    else:
        days, rows, cols = ET_stack.shape
        subset_shape = (rows, cols)
        logger.info("rasterizing ROI")
        mask = geometry_mask([ROI_latlon], subset_shape, subset_affine, invert=True)

        logger.info(f"processing monthly values for year: {year}")
        monthly_means = []

        for j, month in enumerate(range(start_month, end_month + 1)):
            if not exists(monthly_sums_directory):
                makedirs(monthly_sums_directory)

            ET_monthly_filename = join(monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

            # if exists(ET_monthly_filename):
            #     logger.info(f"loading monthly file: {ET_monthly_filename}")
            #     with rasterio.open(ET_monthly_filename, "r") as f:
            #         ET_monthly = f.read(1)
            # else:
            start = datetime(year, month, 1).date()
            logger.info("start creation_date: " + start.strftime("%Y-%m-%d"))
            start_index = start.timetuple().tm_yday
            logger.info(f"start index: {start_index}")
            # end = datetime(year, month + 1, 1).date()
            end = start + relativedelta(months=1)
            logger.info("end creation_date: " + end.strftime("%Y-%m-%d"))
            end_index = end.timetuple().tm_yday
            logger.info(f"end index: {end_index}")
            ET_month_stack = ET_stack[start_index:end_index, :, :]
            ET_monthly = np.nansum(ET_month_stack, axis=0)

            # ET_nan_proportion = np.nanmean((np.sum(np.where(np.isnan(ET_month_stack), 1, 0), axis=0) / ET_month_stack.shape[0])[mask])


            # profile = {
            #     "driver": "GTiff",
            #     "count": 1,
            #     "width": cols,
            #     "height": rows,
            #     "compress": "LZW",
            #     "dtype": np.float32,
            #     "transform": subset_affine,
            #     "crs": CRS}

            # with rasterio.open(ET_monthly_filename, "w", **profile) as f:
            #     f.write(ET_monthly.astype(np.float32), 1)
            logger.info(f"writing monthly ET: {ET_monthly_filename}")
            subset_geometry = rt.RasterGrid.from_affine(subset_affine, rows, cols, CRS)
            ET_monthly_raster = rt.Raster(array=ET_monthly, geometry=subset_geometry)
            ET_monthly_raster.to_geotiff(ET_monthly_filename)


            PET_monthly_filename = join(monthly_sums_directory,
                                        f"{year:04d}_{month:02d}_{ROI_name}_PET_monthly_sum.tif")

            # if exists(PET_monthly_filename):
            #     logger.info(f"loading monthly file: {PET_monthly_filename}")
            #     with rasterio.open(PET_monthly_filename, "r") as f:
            #         PET_monthly = f.read(1)
            # else:
            start = datetime(year, month, 1).date()
            logger.info("start creation_date: " + start.strftime("%Y-%m-%d"))
            start_index = start.timetuple().tm_yday
            logger.info(f"start index: {start_index}")
            # end = datetime(year, month + 1, 1).date()
            end = start + relativedelta(months=1)
            logger.info("end creation_date: " + end.strftime("%Y-%m-%d"))
            end_index = end.timetuple().tm_yday
            logger.info(f"end index: {end_index}")
            PET_month_stack = PET_stack[start_index:end_index, :, :]
            PET_monthly = np.nansum(PET_month_stack, axis=0)

            # PET_nan_proportion = np.nanmean((np.sum(np.where(np.isnan(PET_month_stack), 1, 0), axis=0) / PET_month_stack.shape[0])[mask])

            # profile = {
            #     "driver": "GTiff",
            #     "count": 1,
            #     "width": cols,
            #     "height": rows,
            #     "compress": "LZW",
            #     "dtype": np.float32,
            #     "transform": subset_affine,
            #     "crs": CRS}
            

            # with rasterio.open(PET_monthly_filename, "w", **profile) as f:
            #     f.write(PET_monthly.astype(np.float32), 1)
            logger.info(f"writing monthly PET: {PET_monthly_filename}")
            subset_geometry = rt.RasterGrid.from_affine(subset_affine, rows, cols, CRS)
            PET_monthly_raster = rt.Raster(array=PET_monthly, geometry=subset_geometry)
            PET_monthly_raster.to_geotiff(PET_monthly_filename)

            ET_values = np.array(ET_monthly[mask]).flatten()
            PET_values = np.array(PET_monthly[mask]).flatten()

            ET_monthly_mean = np.nanmean(ET_values)
            PET_monthly_mean = np.nanmean(PET_values)

            # ET_value_count = len(ET_values)
            # PET_value_count = len(PET_values)

            # print(f"mask.shape: {mask.shape}")
            # print(f"ET_month_stack.shape: {ET_month_stack.shape}")

            # ET_nan_count = np.count_nonzero(np.isnan(ET_values))
            # ET_nan_proportion = ET_nan_count / ET_value_count

            # PET_nan_count = np.count_nonzero(np.isnan(PET_values))
            # PET_nan_proportion = PET_nan_count / PET_value_count

            # ET_monthly_mean = np.nanmean(ET_monthly[mask])
            # PET_monthly_mean = np.nanmean(PET_monthly[mask])

            # monthly_means.append([year, month, ET_monthly_mean, PET_monthly_mean, ET_nan_proportion, PET_nan_proportion])
            monthly_means.append([year, month, ET_monthly_mean, PET_monthly_mean])

        if not exists(monthly_means_directory):
            makedirs(monthly_means_directory)

        monthly_means_df = pd.DataFrame(monthly_means, columns=["Year", "Month", "ET", "PET"])
        # monthly_means_df = pd.DataFrame(monthly_means, columns=["Year", "Month", "ET", "PET", "ET_nan", "PET_nan"])
        logger.info(f"writing monthly means: {monthly_means_filename}")
        monthly_means_df.to_csv(monthly_means_filename)
    
    return monthly_means_df
