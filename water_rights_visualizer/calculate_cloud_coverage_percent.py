from os import makedirs, listdir, remove
from os.path import exists, isfile, join, basename, splitext
from glob import glob
import csv
import numpy as np
import pandas as pd
from shapely.geometry import Polygon
import rasterio
from rasterio.mask import mask, raster_geometry_mask
from logging import getLogger
import re
import datetime

logger = getLogger(__name__)


def get_days_in_month(year, month):
    # Calculate the first day of the next month
    if month == 12:
        next_month = datetime.date(year + 1, 1, 1)
    else:
        next_month = datetime.date(year, month + 1, 1)

    # Subtract one day to get the last day of the current month
    last_day_of_month = next_month - datetime.timedelta(days=1)

    return last_day_of_month.day


def calculate_cloud_coverage_percent(
    ROI_geometry: Polygon, subset_directory: str, nan_subset_directory: str, monthly_nan_directory: str
):
    """
    Calculate the percentage of NaN values in each subset file within the given directory based on CCOUNT data.

    Args:
        ROI_geometry (Polygon): The region of interest polygon used for masking the subset files.
        year (int): The year for which to calculate the cloud coverage percentage.
        monthly_nan_directory (str): The directory to save the monthly average NaN values.

    Returns:
        None
    """
    if not exists(monthly_nan_directory):
        makedirs(monthly_nan_directory)

    if not exists(nan_subset_directory):
        makedirs(nan_subset_directory)

    yearly_ccount_percentages = {}

    subset_files = glob(f"{subset_directory}/*_ET_CCOUNT_subset.tif")
    for ccount_subset_file in subset_files:
        filename = basename(ccount_subset_file)
        match = re.match(r"(\d{4})\.(\d{2})\.(\d{2}).*_ET_CCOUNT_subset\.tif", filename)
        year = match.group(1)
        month = match.group(2)
        if not yearly_ccount_percentages.get(year):
            yearly_ccount_percentages[year] = {}

        days_in_month = get_days_in_month(int(year), int(month))

        nan_masked_subset_file = None
        with rasterio.open(ccount_subset_file) as subset_tiles:
            # Masking the ET subset file with the ROI_for_nan polygon
            out_image, out_transform = mask(subset_tiles, ROI_geometry, crop=False)
            out_meta = subset_tiles.meta.copy()
            out_meta.update(
                {
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                }
            )
            nan_masked_subset_file = splitext(nan_subset_directory + "/" + basename(subset_tiles.name))[0] + "_nan.tif"
            # Saving the masked subset as a new file in the nan_subset_directory
            with rasterio.open(nan_masked_subset_file, "w", **out_meta) as dest:
                dest.write(out_image)

        if not nan_masked_subset_file:
            logger.error(f"Failed to create nan masked subset file for {filename}")
            continue

        with rasterio.open(nan_masked_subset_file) as ccount_subset_src:
            ccount_data = ccount_subset_src.read(1)
            ccount_data = ccount_data[ccount_data != ccount_subset_src.nodata]
            ccount_average = np.mean(ccount_data)
            ccount_percent = ccount_average / days_in_month

            yearly_ccount_percentages[year][month] = ccount_percent

    for year, month_percentages in yearly_ccount_percentages.items():
        # If there's already a CSV file for the year, fill that in, but prefer the new data
        monthly_ccount_percent_csv = f"{monthly_nan_directory}/{year}.csv"
        existing_nan_percent_csv = None
        if exists(monthly_ccount_percent_csv):
            existing_nan_percent_csv = pd.read_csv(monthly_ccount_percent_csv)

        monthly_ccount = pd.DataFrame(columns=["year", "month", "percent_nan"])
        for month in range(1, 13):
            # Pad month with 0 if less than 10
            month_key = f"{month:02d}"
            percentage = month_percentages.get(month_key, None)
            if percentage is None and existing_nan_percent_csv is not None:
                existing_row = existing_nan_percent_csv.loc[existing_nan_percent_csv["month"] == month_key]
                if not existing_row.empty:
                    percentage = existing_row["percent_nan"].values[0]

            if percentage is None:
                percentage = 1
            rounded_percentage = round(percentage * 100, 2)
            monthly_ccount.loc[len(monthly_ccount)] = [str(year), month, rounded_percentage]

        monthly_ccount.to_csv(monthly_ccount_percent_csv, index=False)
