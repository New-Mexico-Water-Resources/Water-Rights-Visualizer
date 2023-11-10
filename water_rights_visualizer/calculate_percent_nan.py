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

logger = getLogger(__name__)

def calculate_percent_nan(
        ROI_for_nan: Polygon,
        subset_directory: str,
        nan_subset_directory: str,
        monthly_nan_directory: str):
    if not exists(nan_subset_directory):
        makedirs(nan_subset_directory)
    
    nan_subsets = (nan_subset_directory)

    for items in listdir(subset_directory):
        if items.endswith('_ET_subset.tif') and isfile(join(subset_directory, items)):
            with rasterio.open(join(subset_directory, items)) as p:
                out_image, out_transform = mask(p, ROI_for_nan, crop=False)
                out_meta = p.meta.copy()
                out_meta.update({"driver": "GTiff",
                                    "height": out_image.shape[1],
                                    "width": out_image.shape[2],
                                    "transform": out_transform})
                with rasterio.open(splitext(nan_subsets + "/" + basename(p.name))[0] + "_nan.tif", "w",
                                    **out_meta) as dest:
                    dest.write(out_image)

    a_subset = rasterio.open(subset_directory + "/" + listdir(subset_directory)[0])

    out_image, out_transform = mask(a_subset, ROI_for_nan, invert=True)
    out_meta = a_subset.meta.copy()
    out_meta.update({"driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform})
    with rasterio.open(subset_directory + "/masked_area.tif", "w", **out_meta) as dest2:
        dest2.write(out_image)

    roi_mask = raster_geometry_mask(a_subset, ROI_for_nan, invert=True)
    open_mask = (rasterio.open(subset_directory + "/masked_area.tif"))
    area_mask = open_mask.read()
    area = np.count_nonzero(((area_mask[0][roi_mask[0]])) == 0)
    ET_subset = rasterio.open(nan_subsets + "/" + listdir(nan_subsets)[0])
    base_name = basename(ET_subset.name)
    file_name = splitext(base_name)[0]
    subset_in_mskdir = (rasterio.open(nan_subsets + '/' + file_name + ".tif"))
    percent_nan = []
    msk_subsets = glob(join(nan_subsets, '*.tif'))

    def read_file(file):
        with rasterio.open(file) as src:
            return (src.read())

    array_list = [read_file(x) for x in msk_subsets]
    
    for subsets in array_list:
        nan = np.count_nonzero((np.isnan(subsets[0][roi_mask[0]])))
        count_nan = []
        count_nan.append(nan)

        for nans in count_nan:
            if area == 0:
                ratio_of_nan = (nans / 1)
                percent_of_nan = ratio_of_nan * 100
                percent_nan.append(percent_of_nan)
            else:
                ratio_of_nan = (nans / area)
                percent_of_nan = ratio_of_nan * 100
                percent_nan.append(percent_of_nan)

    dates = []

    for msk_subset in msk_subsets:
        with rasterio.open(msk_subset) as t:
            paths = basename(t.name)
            date_split = paths.split("_")[0]
            dates.append(date_split)

    years = []
    months = []
    days = []

    for date_time in dates:
        msk_year = date_time.split(".")[0]
        years.append(msk_year)
        msk_month = date_time.split(".")[1]
        months.append(msk_month)
        msk_day = date_time.split(".")[2]
        days.append(msk_day)

    if not exists(monthly_nan_directory):
        makedirs(monthly_nan_directory)

    nan_csv = "nan_avg.csv"
    nan_monthly_csv = "nan_monthly_avg.csv"
    nan_folder = join(monthly_nan_directory, nan_csv)
    nan_monthly_folder = join(monthly_nan_directory, nan_monthly_csv)

    with open(nan_folder, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['percent_nan', 'year', 'month'])
        rows = zip(percent_nan, years, months)

        for row in rows:
            writer.writerow(row)

    nan_avg = list()
    nanavg = pd.read_csv(nan_folder)
    group = nanavg.groupby(['year', 'month'])
    monthavg = group.aggregate({'percent_nan': np.mean})
    nan_avg.append(monthavg)
    conavg = pd.concat(nan_avg, ignore_index=False)
    conavg.to_csv(nan_monthly_folder)
    sort_order = pd.read_csv(nan_monthly_folder)
    sort_ascend = sort_order.sort_values('year', ascending=False)
    nan_monthly_avg = pd.read_csv(nan_monthly_folder)
    cols_nan = nan_monthly_avg.columns
    nan_monthly_avg['Year'] = nan_monthly_avg['year']

    for years in set(nan_monthly_avg.Year):
        new_csv_by_year = monthly_nan_directory + '/' + str(years) + ".csv"
        nan_monthly_avg.loc[nan_monthly_avg.Year == years].to_csv(new_csv_by_year, index=False, columns=cols_nan)
    
    remove(nan_monthly_folder)
    remove(nan_folder)
