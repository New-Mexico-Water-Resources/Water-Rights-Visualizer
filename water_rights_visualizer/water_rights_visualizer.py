#!/usr/bin/env python
# coding: utf-8
import contextlib
import csv
import logging
import os
import sys
import tempfile
from abc import abstractmethod
from datetime import date as dt
from datetime import datetime, date
from glob import glob
from os import makedirs, scandir, listdir, remove, chdir
from os.path import basename, isdir, abspath, dirname, splitext
from os.path import join, exists, isfile
from pathlib import Path
from typing import Union

import geojson
import geopandas as gpd
import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import seaborn as sns
from affine import Affine
from area import area
from dateutil import parser
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
from pydrive2.drive import GoogleDrive
from rasterio.features import geometry_mask
from rasterio.mask import raster_geometry_mask, mask
from rasterio.warp import reproject
from rasterio.windows import Window
from rasterio.windows import transform as window_transform
from scipy.interpolate import interp1d
from shapely.geometry import MultiPolygon
from shapely.geometry import Point

from water_rights_visualizer.google_drive import google_drive_login

logger = logging.getLogger(__name__)

ARD_TILES_FILENAME = join(abspath(dirname(__file__)), "ARD_tiles.geojson")

TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01
BUFFER_METERS = 2000
BUFFER_DEGREES = 0.001
CELL_SIZE_DEGREES = 0.0003
CELL_SIZE_METERS = 30

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
UTM = "+proj=utm +zone=13 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"


class FileUnavailable(Exception):
    pass


class DataSource:
    @abstractmethod
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        pass


class FilepathSource(DataSource):
    def __init__(self, directory: str):
        self.directory = directory

    def date_directory(self, acquisition_date: Union[date, str]) -> str:
        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        date_directory = join(self.directory, f"{acquisition_date:%Y.%m.%d}")

        return date_directory

    @contextlib.contextmanager
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        raster_directory = self.date_directory(acquisition_date)
        pattern = join(raster_directory, "**",
                       f"*_{tile}_*_{variable_name}.tif")
        logger.info(f"searching pattern: {pattern}")
        matches = sorted(glob(pattern, recursive=True))

        if len(matches) == 0:
            raise FileUnavailable(f"no files found for tile: {tile}")

        input_filename = matches[0]
        logger.info(f"{tile}: {input_filename}")

        yield input_filename


class GoogleSource(DataSource):
    def __init__(self, drive: GoogleDrive = None, temporary_directory: str = None, ID_table_filename: str = None):
        if drive is None:
            drive = google_drive_login()

        if temporary_directory is None:
            temporary_directory = tempfile.gettempdir()

        if ID_table_filename is None:
            ID_table_filename = join(
                abspath(dirname(__file__)), "google_drive_file_IDs.csv")

        ID_table = pd.read_csv(ID_table_filename)

        self.drive = drive
        self.temporary_directory = temporary_directory
        self.ID_table = ID_table

    @contextlib.contextmanager
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        acquisition_date = acquisition_date.strftime("%Y-%m-%d")

        filtered_table = self.ID_table[self.ID_table.apply(lambda row: row.tile == int(
            tile) and row.variable == variable_name and parser.parse(str(row.date)).date().strftime(
            "%Y-%m-%d") == acquisition_date, axis=1)]

        if len(filtered_table) == 0:
            raise FileUnavailable(f"no files found for tile: {tile}")

        print(filtered_table)
        print(filtered_table.iloc[0])

        filename_base = str(filtered_table.iloc[0].filename)
        file_ID = str(filtered_table.iloc[0].file_ID)

        logger.info(
            f"retrieving {filename_base} from Google Drive ID {file_ID}")
        filename = join(self.temporary_directory, filename_base)

        google_drive_file = self.drive.CreateFile(metadata={"id": file_ID})
        google_drive_file.GetContentFile(filename=filename)

        logger.info(f"temporary file: {filename}")

        yield filename

        logger.info(f"removing temporary file: {filename}")
        os.remove(filename)


def generate_patch(polygon, affine):
    if isinstance(polygon, MultiPolygon):
        polygon = list(polygon)[0]

    polygon_indices = [
        ~affine * coords for coords in polygon.exterior.coords]
    patch = Polygon(polygon_indices, fill=None, color="black", linewidth=1)

    return patch


def inventory(source_directory):
    # logger.info(f"searching data: {source_directory}")
    date_directories = sorted(glob(join(source_directory, "*")))
    date_directories = [
        directory for directory in date_directories if isdir(directory)]
    dates_available = [datetime.strptime(
        basename(directory), "%Y.%m.%d").date() for directory in date_directories]
    years_available = list(
        set(sorted([date_step.year for date_step in dates_available])))

    return years_available, dates_available


def generate_stack(
        ROI_name,
        ROI_latlon,
        year,
        ROI_acres,
        source_directory,
        subset_directory,
        dates_available,
        stack_filename,
        target_CRS=None):
    if target_CRS is None:
        target_CRS = WGS84

    # logger.info(f"year: {year}")

    if exists(stack_filename):
        # logger.info(f"loading stack: {stack_filename}")
        logger.info(f"loading stack: {stack_filename}\n")

        with h5py.File(stack_filename, "r") as stack_file:
            ET_stack = np.array(stack_file["ET"])
            PET_stack = np.array(stack_file["PET"])
            affine = Affine(*list(stack_file["affine"]))

        return ET_stack, PET_stack, affine

    # logger.info(f"generating stack")

    ET_sparse_stack = None
    ESI_sparse_stack = None

    dates_in_year = [
        date_step
        for date_step
        in dates_available
        if date_step.year == year
    ]

    # logger.info("dates_in_year:")
    # logger.info(dates_in_year)

    if len(dates_in_year) == 0:
        raise ValueError(f"no dates for year: {year}")

    for date_step in dates_in_year:
        # logger.info(f"date: {date_step.strftime('%Y-%m-%d')}")

        if not exists(subset_directory):
            makedirs(subset_directory)

        ET_subset_filename = join(
            subset_directory, f"{date_step.strftime('%Y.%m.%d')}_{ROI_name}_ET_subset.tif")
        ESI_subset_filename = join(
            subset_directory, f"{date_step.strftime('%Y.%m.%d')}_{ROI_name}_ESI_subset.tif")

        source_raster_directory = join(
            source_directory, date_step.strftime("%Y.%m.%d"))

        try:
            ET_subset, affine = generate_subset(
                source_raster_directory,
                ROI_latlon,
                ROI_acres,
                "ET",
                subset_filename=ET_subset_filename,
                target_CRS=target_CRS
            )
        except Exception as e:
            logger.info(e)
            # logger.info(f"problem generating ET subset for date: {date_step.strftime('%Y-%m-%d')}")
            continue

        try:
            ESI_subset, affine = generate_subset(
                source_raster_directory,
                ROI_latlon,
                ROI_acres,
                "ESI",
                subset_filename=ESI_subset_filename,
                target_CRS=target_CRS
            )
        except Exception as e:
            logger.info(e)
            # logger.info(f"problem generating ESI subset for date: {date_step.strftime('%Y-%m-%d')}")
            continue

        subset_shape = ESI_subset.shape
        rows, cols = subset_shape
        month = date_step.month
        day = date_step.day

        if ET_sparse_stack is None:
            days_in_year = (datetime(year, 12, 31) -
                            datetime(year, 1, 1)).days + 1
            ET_sparse_stack = np.full(
                (days_in_year, rows, cols), np.nan, dtype=np.float32)

        if ESI_sparse_stack is None:
            days_in_year = (datetime(year, 12, 31) -
                            datetime(year, 1, 1)).days + 1
            ESI_sparse_stack = np.full(
                (days_in_year, rows, cols), np.nan, dtype=np.float32)

        day_of_year = (datetime(year, month, day) -
                       datetime(year, 1, 1)).days - 1

        ET_doy_image = ET_sparse_stack[day_of_year, :, :]
        ET_sparse_stack[day_of_year, :, :] = np.where(
            np.isnan(ET_doy_image), ET_subset, ET_doy_image)

        ESI_doy_image = ESI_sparse_stack[day_of_year, :, :]
        ESI_sparse_stack[day_of_year, :, :] = np.where(
            np.isnan(ESI_doy_image), ESI_subset, ESI_doy_image)

    if ET_sparse_stack is None:
        raise ValueError("no ET stack generated")
        # texts("no ET stack generated\n")

    if ESI_sparse_stack is None:
        raise ValueError("no ESI stack generated")
        # texts("no ESI stack generated\n")

    PET_sparse_stack = ET_sparse_stack / ESI_sparse_stack

    # logger.info(f"interpolating ET stack for year: {year}")
    ET_stack = interpolate_stack(ET_sparse_stack)
    PET_stack = interpolate_stack(PET_sparse_stack)

    stack_directory = dirname(stack_filename)

    if not exists(stack_directory):
        makedirs(stack_directory)

    # logger.info(f"writing stack: {stack_filename}")
    with h5py.File(stack_filename, "w") as stack_file:
        stack_file["ET"] = ET_stack
        stack_file["PET"] = PET_stack

        stack_file["affine"] = (
            affine.a,
            affine.b,
            affine.c,
            affine.d,
            affine.e,
            affine.f
        )

    return ET_stack, PET_stack, affine


def interpolate_stack(stack):
    days, rows, cols = stack.shape
    filled_stack = np.full((days, rows, cols), np.nan, dtype=np.float32)

    for row in range(rows):
        for col in range(cols):
            pixel_timeseries = stack[:, row, col]
            x = np.arange(days)
            known_indices = ~np.isnan(pixel_timeseries)
            known_days = x[known_indices]

            if len(known_days) < 3:
                continue

            pixel_timeseries = pixel_timeseries[known_indices]
            f = interp1d(known_days, pixel_timeseries, axis=0,
                         kind="nearest", fill_value="extrapolate")
            y = f(x)
            filled_stack[:, row, col] = y

    return filled_stack


def ROI_area(ROI, working_directory):
    try:
        ROI_gpd = gpd.read_file(ROI).to_crs(WGS84)
        ROI_acre = ROI_gpd['Acres']

    except KeyError:

        ROI_gpd = gpd.read_file(ROI).to_crs(WGS84)
        filename = basename(ROI)
        expt = ROI_gpd.to_file(filename, driver="GeoJSON")
        impt = open(filename)
        ROI_base = geojson.load(impt)
        ROI_geom = ROI_base['features'][0]['geometry']
        ROI_acre = area(ROI_geom) * 0.000247105

    return (ROI_acre)


def process_monthly(
        ET_stack,
        PET_stack,
        ROI_latlon,
        ROI_name,
        subset_affine,
        CRS,
        year,
        monthly_sums_directory,
        monthly_means_directory):
    monthly_means_filename = join(
        monthly_means_directory, f"{year}_monthly_means.csv")

    if exists(monthly_means_filename):
        # logger.info(f"loading monthly means: {monthly_means_filename}")
        monthly_means_df = pd.read_csv(monthly_means_filename)
    else:
        days, rows, cols = ET_stack.shape
        subset_shape = (rows, cols)
        # logger.info("rasterizing ROI")
        mask = geometry_mask([ROI_latlon], subset_shape,
                             subset_affine, invert=True)

        # logger.info(f"processing monthly values for year: {year}")
        monthly_means = []

        for j, month in enumerate(range(3, 11)):
            if not exists(monthly_sums_directory):
                makedirs(monthly_sums_directory)

            ET_monthly_filename = join(
                monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

            if exists(ET_monthly_filename):
                # logger.info(f"loading monthly file: {ET_monthly_filename}")
                with rasterio.open(ET_monthly_filename, "r") as f:
                    ET_monthly = f.read(1)
            else:
                start = datetime(year, month, 1).date()
                # logger.info("start date: " + start.strftime("%Y-%m-%d"))
                start_index = start.timetuple().tm_yday
                # logger.info(f"start index: {start_index}")
                end = datetime(year, month + 1, 1).date()
                # logger.info("end date: " + end.strftime("%Y-%m-%d"))
                end_index = end.timetuple().tm_yday
                # logger.info(f"end index: {end_index}")
                ET_month_stack = ET_stack[start_index:end_index, :, :]
                ET_monthly = np.nansum(ET_month_stack, axis=0)

                # plt.imshow(ET_monthly)
                # plt.colorbar()
                # plt.title(f"{year:04d}-{month:02d}")
                # plt.show()

                # logger.info(f"writing ET monthly file: {ET_monthly_filename}")

                profile = {
                    "driver": "GTiff",
                    "count": 1,
                    "width": cols,
                    "height": rows,
                    "compress": "LZW",
                    "dtype": np.float32,
                    "transform": subset_affine,
                    "crs": CRS}

                with rasterio.open(ET_monthly_filename, "w", **profile) as f:
                    f.write(ET_monthly.astype(np.float32), 1)

            PET_monthly_filename = join(monthly_sums_directory,
                                        f"{year:04d}_{month:02d}_{ROI_name}_PET_monthly_sum.tif")

            if exists(PET_monthly_filename):
                # logger.info(f"loading monthly file: {PET_monthly_filename}")
                with rasterio.open(PET_monthly_filename, "r") as f:
                    PET_monthly = f.read(1)
            else:
                start = datetime(year, month, 1).date()
                # logger.info("start date: " + start.strftime("%Y-%m-%d"))
                start_index = start.timetuple().tm_yday
                # logger.info(f"start index: {start_index}")
                end = datetime(year, month + 1, 1).date()
                # logger.info("end date: " + end.strftime("%Y-%m-%d"))
                end_index = end.timetuple().tm_yday
                # logger.info(f"end index: {end_index}")
                PET_month_stack = PET_stack[start_index:end_index, :, :]
                PET_monthly = np.nansum(PET_month_stack, axis=0)

                # plt.imshow(PET_monthly)
                # plt.colorbar()
                # plt.title(f"{year:04d}-{month:02d}")
                # plt.show()

                # logger.info(f"writing PET monthly file: {PET_monthly_filename}")

                profile = {
                    "driver": "GTiff",
                    "count": 1,
                    "width": cols,
                    "height": rows,
                    "compress": "LZW",
                    "dtype": np.float32,
                    "transform": subset_affine,
                    "crs": CRS}

                with rasterio.open(PET_monthly_filename, "w", **profile) as f:
                    f.write(PET_monthly.astype(np.float32), 1)

            ET_monthly_mean = np.nanmean(ET_monthly[mask])
            PET_monthly_mean = np.nanmean(PET_monthly[mask])
            monthly_means.append(
                [year, month, ET_monthly_mean, PET_monthly_mean])

        if not exists(monthly_means_directory):
            makedirs(monthly_means_directory)

        monthly_means_df = pd.DataFrame(
            monthly_means, columns=["Year", "Month", "ET", "PET"])
        # logger.info(f"writing monthly means: {monthly_means_filename}")
        monthly_means_df.to_csv(monthly_means_filename)

    return monthly_means_df


def calculate_percent_nan(
        ROI_for_nan,
        subset_directory,
        nan_subset_directory,
        monthly_nan_directory):
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

    a_subset = rasterio.open(
        subset_directory + "/" + listdir(subset_directory)[0])

    out_image, out_transform = mask(a_subset, ROI_for_nan, invert=True)
    out_meta = a_subset.meta.copy()
    out_meta.update({"driver": "GTiff",
                     "height": out_image.shape[1],
                     "width": out_image.shape[2],
                     "transform": out_transform})
    with rasterio.open(subset_directory + "/masked_area.tif", "w", **out_meta) as dest2:
        dest2.write(out_image)

    roi_mask = raster_geometry_mask(a_subset, ROI_for_nan, invert=True)
    # logger.info(f"roi_mask:")
    # logger.info(roi_mask)
    open_mask = (rasterio.open(subset_directory + "/masked_area.tif"))
    # logger.info(f"open_mask:")
    # logger.info(open_mask)
    area_mask = open_mask.read()
    # logger.info(f"area_mask:")
    # logger.info(area_mask)
    # area = np.count_nonzero((area_mask[0][roi_mask[0]]))
    area = np.count_nonzero(((area_mask[0][roi_mask[0]])) == 0)
    # logger.info(f"area:")
    # logger.info(area)

    ET_subset = rasterio.open(nan_subsets + "/" + listdir(nan_subsets)[0])
    base_name = basename(ET_subset.name)
    file_name = splitext(base_name)[0]
    subset_in_mskdir = (rasterio.open(
        nan_subsets + '/' + file_name + ".tif"))

    percent_nan = []
    msk_subsets = glob(join(nan_subsets, '*.tif'))

    def read_file(file):
        with rasterio.open(file) as src:
            return (src.read())

    array_list = [read_file(x) for x in msk_subsets]
    # logger.info(f"array_list:")
    # logger.info(array_list)
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
        nan_monthly_avg.loc[nan_monthly_avg.Year == years].to_csv(
            new_csv_by_year, index=False, columns=cols_nan)

    remove(nan_monthly_folder)
    remove(nan_folder)


def generate_figure(
        ROI_name,
        ROI_latlon,
        ROI_acres,
        date,
        year,
        vmin,
        vmax,
        affine,
        main_df,
        monthly_sums_directory,
        figure_filename):
    fig = plt.figure()
    fig.suptitle(
        (f"Evapotranspiration For {ROI_name} - {year} - {ROI_acres} acres"), fontsize=14)
    grid = plt.GridSpec(3, 4, wspace=0.4, hspace=0.3)

    for i, month in enumerate((3, 4, 5, 6, 7, 8, 9, 10)):
        # logger.info(f"rendering month: {month} sub-figure: {i}")
        subfigure_title = datetime(year, month, 1).date().strftime("%Y-%m")
        # logger.info(f"sub-figure title: {subfigure_title}")
        ET_monthly_filename = join(
            monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

        if not exists(ET_monthly_filename):
            raise IOError(
                f"monthly sum file not found: {ET_monthly_filename}")

        # logger.info(f"loading monthly file: {ET_monthly_filename}")
        with rasterio.open(ET_monthly_filename, "r") as f:
            monthly = f.read(1)

        ax = plt.subplot(grid[int(i / 4), i % 4])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        # logger.info(f"min: {np.nanmin(monthly)} mean: {np.nanmean(monthly)} max: {np.nanmax(monthly)}")

        ET_COLORS = [
            "#f6e8c3",
            "#d8b365",
            "#99974a",
            "#53792d",
            "#6bdfd2",
            "#1839c5"
        ]

        cmap = LinearSegmentedColormap.from_list("ET", ET_COLORS)
        im = ax.imshow(monthly, vmin=vmin, vmax=vmax, cmap=cmap)
        ax.add_patch(generate_patch(ROI_latlon, affine))
        ax.set_title(subfigure_title)

    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    fig.colorbar(im, cax=cbar_ax, ticks=[
    ], label=f'Low                                                            High')

    ax = plt.subplot(grid[2, :])
    df = main_df[main_df["Year"] == year]
    x = df["Month"]
    y = df["PET"]
    y2 = df["ET"]
    ci = df["percent_nan"]
    sns.lineplot(x=x, y=y, ax=ax, color="blue", label="PET")
    sns.lineplot(x=x, y=y2, ax=ax, color="green", label="ET")
    ax.fill_between(x, (y - ci), (y + ci), color='b', alpha=.1)
    ax.fill_between(x, (y2 - ci), (y2 + ci), color='g', alpha=.1)
    plt.legend(labels=['ET'], loc='upper right')
    ax.legend(loc='upper left', fontsize=6)
    ax.set(xlabel="Month", ylabel="ET (mm)")
    ymin = min(min(main_df["ET"]), min(main_df["ET"]))
    ymax = max(max(main_df["PET"]), max(main_df["PET"]))
    ylim = (int(ymin), int(ymax + 10))
    ax.set(ylim=ylim)
    ax.set_yticks([int(ymin), int(ymax) + 10])
    ax.set_yticklabels(['Low', 'High'])

    plt.title(f"Area of Interest Average Monthly Water Use", fontsize=10)
    caption = "ET and PET calculated by the PT-JPL retrieval: Fisher et al. (2008) with Landsat data"
    caption2 = f"Visualization created {date}"
    plt.figtext(0.48, 0.001, caption, wrap=True, verticalalignment='bottom',
                horizontalalignment='center', fontsize=5)
    plt.figtext(0.93, 0.001, caption2, wrap=True,
                verticalalignment='bottom', horizontalalignment='right', fontsize=5)
    plt.tight_layout()

    logger.info("saving figure: {figure_filename}")
    plt.savefig(figure_filename, dpi=300)


def water_rights(
        ROI,
        input_directory,
        output_directory,
        start_year=None,
        end_year=None,
        ROI_name=None,
        source_directory=None,
        figure_directory=None,
        working_directory=None,
        subset_directory=None,
        nan_subset_directory=None,
        stack_directory=None,
        reference_directory=None,
        monthly_sums_directory=None,
        monthly_means_directory=None,
        monthly_nan_directory=None,
        target_CRS=None,
        remove_working_directory=None):
    ROI_base = splitext(basename(ROI))[0]
    DEFAULT_FIGURE_DIRECTORY = Path(f"{output_directory}/figures")
    DEFAULT_SOURCE_DIRECTORY = Path(f"{input_directory}")
    DEFAULT_SUBSET_DIRECTORY = Path(f"{output_directory}/subset/{ROI_base}")
    DEFAULT_NAN_SUBSET_DIRECTORY = Path(
        f"{output_directory}/nan_subsets/{ROI_base}")
    DEFAULT_MONTHLY_DIRECTORY = Path(f"{output_directory}/monthly/{ROI_base}")
    DEFAULT_STACK_DIRECTORY = Path(f"{output_directory}/stack/{ROI_base}")
    DEFAULT_MONTHLY_NAN_DIRECTORY = Path(
        f"{output_directory}/monthly_nan/{ROI_base}")
    DEFAULT_MONTHLY_MEANS_DIRECTORY = Path(
        f"{output_directory}/monthly_means/{ROI_base}")

    if ROI_name is None:
        ROI_name = splitext(basename(ROI))[0]

    if working_directory is None:
        working_directory = ROI_name

    if remove_working_directory is None:
        remove_working_directory = True

    if subset_directory is None:
        subset_directory = join(
            working_directory, DEFAULT_SUBSET_DIRECTORY)

    if nan_subset_directory is None:
        nan_subset_directory = join(
            working_directory, DEFAULT_NAN_SUBSET_DIRECTORY)

    if monthly_sums_directory is None:
        monthly_sums_directory = join(
            working_directory, DEFAULT_MONTHLY_DIRECTORY)

    if stack_directory is None:
        stack_directory = join(working_directory, DEFAULT_STACK_DIRECTORY)

    if monthly_means_directory is None:
        monthly_means_directory = join(
            working_directory, DEFAULT_MONTHLY_MEANS_DIRECTORY)

    if monthly_nan_directory is None:
        monthly_nan_directory = join(
            working_directory, DEFAULT_MONTHLY_NAN_DIRECTORY)

    if source_directory is None:
        source_directory = DEFAULT_SOURCE_DIRECTORY

    if figure_directory is None:
        figure_directory = DEFAULT_FIGURE_DIRECTORY

    if target_CRS is None:
        target_CRS = WGS84

    logger.info(f"ROI name: {ROI_name}")
    logger.info(f"loading ROI: {ROI}")
    ROI_latlon = gpd.read_file(ROI).to_crs(WGS84).geometry[0]
    ROI_for_nan = list((gpd.read_file(ROI).to_crs(WGS84)).geometry)
    ROI_acres = round(ROI_area(ROI, working_directory), 2)

    years_available, dates_available = inventory(source_directory)
    monthly_means = []

    if start_year is None:
        start_year = sorted(years_available)[0]

    if end_year is None:
        end_year = sorted(years_available)[-1]

    if start_year == end_year:
        years_x = [start_year]
    else:
        years_x = [*range(int(start_year), int(end_year) + 1)]

    for i, year in enumerate(years_x):
        logger.info(f"processing: {year}")

        stack_filename = join(
            stack_directory, f"{year:04d}_{ROI_name}_stack.h5")

        try:

            ET_stack, PET_stack, affine = generate_stack(
                ROI_name=ROI_name,
                ROI_latlon=ROI_latlon,
                year=year,
                ROI_acres=ROI_acres,
                source_directory=source_directory,
                subset_directory=subset_directory,
                dates_available=dates_available,
                stack_filename=stack_filename,
                target_CRS=target_CRS
            )
        except Exception as e:
            logger.info(e)
            logger.info(f"unable to generate stack for year: {year}")
            continue

        monthly_means.append(process_monthly(
            ET_stack=ET_stack,
            PET_stack=PET_stack,
            ROI_latlon=ROI_latlon,
            ROI_name=ROI_name,
            subset_affine=affine,
            CRS=target_CRS,
            year=year,
            monthly_sums_directory=monthly_sums_directory,
            monthly_means_directory=monthly_means_directory
        ))

        logger.info("Calculating uncertainty\n")

        calculate_percent_nan(
            ROI_for_nan,
            subset_directory,
            nan_subset_directory,
            monthly_nan_directory)

        logger.info("Generating figure\n")

        nan_means = []
        nd = pd.read_csv(f"{monthly_nan_directory}/{year}.csv")
        nan_means.append(nd)
        logger.info(f"application nan means: \n {nan_means}")

        month_means = []
        mm = pd.read_csv(
            f"{monthly_means_directory}/{year}_monthly_means.csv")
        month_means.append(mm)
        logger.info(f"application monthly means: \n {month_means}")

        idx = {'Months': [3, 4, 5, 6, 7, 8, 9, 10]}
        df1 = pd.DataFrame(idx, columns=['Months'])
        df2 = pd.DataFrame(idx, columns=['Months'])

        main_dfa = pd.merge(left=df1, right=mm, how='left',
                            left_on="Months", right_on="Month")
        main_df = pd.merge(left=main_dfa, right=nd,
                           how='left', left_on="Months", right_on="month")
        main_df = main_df.replace(np.nan, 100)
        logger.info(f'main_df: {main_df}')

        monthly_means_df = pd.concat(month_means, axis=0)
        logger.info("monthly_means_df:")
        mean = np.nanmean(monthly_means_df["ET"])
        sd = np.nanstd(monthly_means_df["ET"])
        vmin = max(mean - 2 * sd, 0)
        vmax = mean + 2 * sd

        today = dt.today()
        date = str(today)

        logger.info(f"generating figure for year: {year}")

        figure_output_directory = join(figure_directory, ROI_name)

        if not exists(figure_output_directory):
            makedirs(figure_output_directory)

        figure_filename = join(
            figure_output_directory, f"{year}_{ROI_name}.png")

        if exists(figure_filename):
            logger.info(f"figure already exists: {figure_filename}")
            continue

        try:
            generate_figure(
                ROI_name,
                ROI_latlon,
                ROI_acres,
                date,
                year,
                vmin,
                vmax,
                affine,
                main_df,
                monthly_sums_directory,
                figure_filename
            )
        except Exception as e:
            logger.info(e)
            logger.info(f"unable to generate figure for year: {year}")
            continue


def water_rights_visualizer(boundary_filename: str, input_directory: str, output_directory: str, start_year: int = None,
                            end_year: int = None):
    logger.info(f"boundary file: {boundary_filename}")
    logger.info(f"input directory: {input_directory}")
    logger.info(f"output directory: {output_directory}")

    working_directory = f"{output_directory}"
    chdir(working_directory)
    logger.info(f"working directory: {working_directory}")

    ROI_base = splitext(basename(boundary_filename))[0]
    DEFAULT_ROI_DIRECTORY = Path(f"{boundary_filename}")
    ROI_name = Path(f"{DEFAULT_ROI_DIRECTORY}")

    logger.info(f"target: {ROI_name}")

    ROI = ROI_name
    BUFFER_METERS = 2000
    # BUFFER_DEGREES = 0.001
    CELL_SIZE_DEGREES = 0.0003
    CELL_SIZE_METERS = 30
    TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01
    ARD_TILES_FILENAME = join(abspath(dirname(__file__)), "ARD_tiles.geojson")

    if isfile(ROI):
        water_rights(
            ROI,
            input_directory=input_directory,
            output_directory=output_directory,
            start_year=start_year,
            end_year=end_year,
            ROI_name=None,
            source_directory=None,
            figure_directory=None,
            working_directory=None,
            subset_directory=None,
            nan_subset_directory=None,
            stack_directory=None,
            monthly_sums_directory=None,
            monthly_means_directory=None,
            monthly_nan_directory=None,
            target_CRS=None,
            remove_working_directory=None)

    elif isdir(ROI):
        for items in scandir(ROI):
            if items.name.endswith(".geojson"):
                roi_name = abspath(items)
                water_rights(
                    roi_name,
                    input_directory=input_directory,
                    output_directory=output_directory,
                    start_year=start_year,
                    end_year=end_year,
                    ROI_name=None,
                    source_directory=None,
                    figure_directory=None,
                    working_directory=None,
                    subset_directory=None,
                    nan_subset_directory=None,
                    stack_directory=None,
                    monthly_sums_directory=None,
                    monthly_means_directory=None,
                    monthly_nan_directory=None,
                    target_CRS=None,
                    remove_working_directory=None)
    else:
        logger.info("Not a valid file")


def select_tiles(target_geometry_latlon):
    tiles_df = gpd.read_file(ARD_TILES_FILENAME).to_crs(WGS84)
    selection = tiles_df.intersects(
        target_geometry_latlon.buffer(TILE_SELECTION_BUFFER_RADIUS_DEGREES))
    selected_tiles_df = tiles_df[selection]
    tiles = [item[2:] for item in list(selected_tiles_df["name"])]

    return tiles


def generate_subset(
        raster_directory,
        ROI_latlon,
        ROI_acres,
        variable_name,
        subset_filename,
        cell_size=None,
        buffer_size=None,
        target_CRS=None):
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
        logger.info(
            f"loading existing {variable_name} subset file: {subset_filename}")

        with rasterio.open(subset_filename, "r") as f:
            subset = f.read(1)
            affine = f.transform

        return subset, affine

    logger.info(f"generating {variable_name} subset")

    tiles = select_tiles(ROI_latlon)
    logger.info(f"tiles: {tiles}")
    ROI_projected = gpd.GeoDataFrame(
        {}, geometry=[ROI_latlon], crs=WGS84).to_crs(target_CRS).geometry[0]
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
    output_raster = np.full(
        (target_rows, target_cols), np.nan, dtype=np.float32)

    for tile in tiles:
        pattern = join(raster_directory, "**",
                       f"*_{tile}_*_{variable_name}.tif")
        logger.info(f"searching pattern: {pattern}")
        matches = sorted(glob(pattern, recursive=True))

        if len(matches) == 0:
            logger.info(f"no files found for tile: {tile}")
            files_found = sorted(
                glob(join(raster_directory, '**', '*'), recursive=True))
            tiles_found = sorted(
                set([splitext(basename(filename))[0].split("_")[2] for filename in files_found]))
            logger.info(f"files found: {', '.join(tiles_found)}")
            continue

        input_filename = matches[0]
        logger.info(f"{tile}: {input_filename}")

        with rasterio.open(input_filename, "r") as input_file:
            source_CRS = input_file.crs
            input_affine = input_file.transform

            ul = gpd.GeoDataFrame({}, geometry=[Point(x_min, y_max)], crs=target_CRS).to_crs(
                source_CRS).geometry[0]
            col_ul, row_ul = ~input_affine * (ul.x, ul.y)
            col_ul = int(col_ul)
            row_ul = int(row_ul)

            ur = gpd.GeoDataFrame({}, geometry=[Point(x_max, y_max)], crs=target_CRS).to_crs(
                source_CRS).geometry[0]
            col_ur, row_ur = ~input_affine * (ur.x, ur.y)
            col_ur = int(col_ur)
            row_ur = int(row_ur)

            lr = gpd.GeoDataFrame({}, geometry=[Point(x_max, y_min)], crs=target_CRS).to_crs(
                source_CRS).geometry[0]
            col_lr, row_lr = ~input_affine * (lr.x, lr.y)
            col_lr = int(col_lr)
            row_lr = int(row_lr)

            ll = gpd.GeoDataFrame({}, geometry=[Point(x_min, y_min)], crs=target_CRS).to_crs(
                source_CRS).geometry[0]
            col_ll, row_ll = ~input_affine * (ll.x, ll.y)
            col_ll = int(col_ll)
            row_ll = int(row_ll)

            col_min = min(col_ul, col_ll)
            col_min = max(col_min, 0)
            col_max = max(col_ur, col_lr)

            row_min = min(row_ul, row_ur)
            row_min = max(row_min, 0)
            row_max = max(row_ll, row_lr)

            window = (row_min, row_max), (col_min, col_max)

            if row_min < 0 or col_min < 0 or row_max <= row_min or col_max <= col_min:
                logger.info(
                    f"raster does not intersect target surface: {input_filename}")
                continue

            window = Window.from_slices(*window)
            source_subset = input_file.read(1, window=window)
            source_affine = window_transform(window, input_affine)

        target_surface = np.full(
            (target_rows, target_cols), np.nan, dtype=np.float32)

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

        output_raster = np.where(
            np.isnan(output_raster), target_surface, output_raster)
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


def main(argv=sys.argv):
    boundary_filename = argv[1]
    input_directory = argv[2]
    output_directory = argv[3]

    water_rights_visualizer(
        boundary_filename=boundary_filename,
        input_directory=input_directory,
        output_directory=output_directory
    )


if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
