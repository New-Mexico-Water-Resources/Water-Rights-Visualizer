#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import io
from datetime import datetime
from datetime import date as dt
from glob import glob
from os import makedirs, scandir, listdir, getcwd, remove, chdir
from os.path import basename, isdir, exists, abspath, dirname, splitext
from os.path import join, exists, isfile, split
from shutil import rmtree

#import pyproject
import geojson
import geopandas as gpd
import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import seaborn as sns
import random
import csv

from pathlib import Path
from area import area
from affine import Affine
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
from rasterio.mask import raster_geometry_mask, mask
from rasterio.features import geometry_mask
from rasterio.warp import reproject 
from rasterio.windows import Window
from rasterio.windows import transform as window_transform
from scipy.interpolate import interp1d
from shapely.geometry import MultiPolygon
from shapely.geometry import Point

import PIL.Image
import PIL.ImageTk
from tkinter import *
import tkinter.font as font
from tkinter import filedialog
from tkinter import ttk
from tkinter import scrolledtext


# In[ ]:


def submit():
    
    year_list = []
    source_path = entry_filepath.get()
    roi_path = entry_roi.get()
    
    try:
        start = int(entry_start.get())
        year_list.append(start)
    except ValueError:
        print("Input a valid year")
        texts("Input a valid year")
        
    try:
        end = int(entry_end.get())
        year_list.append(end)
    except ValueError:
        end = entry_start.get()
        #year_list.append(end)
     
    
    output = output_path.get()
    
    #acres = variable.get()
    
    print(year_list)
    
    working_directory = f"{output}"
    chdir(working_directory)
    
    ROI_base = splitext(basename(roi_path))[0]
    DEFAULT_ROI_DIRECTORY = Path(f"{roi_path}")
    ROI_name = Path(f"{DEFAULT_ROI_DIRECTORY}")
    ROI = ROI_name
    
    WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
    UTM = "+proj=utm +zone=13 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    BUFFER_METERS = 2000
    #BUFFER_DEGREES = 0.001
    CELL_SIZE_DEGREES = 0.0003
    CELL_SIZE_METERS = 30
    TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01
    
    def select_tiles(target_geometry_latlon):
        tiles_df = gpd.read_file(join(abspath(dirname(__file__)), "water_rights_visualizer", "ARD_tiles.geojson")).to_crs(WGS84)
        selection = tiles_df.intersects(target_geometry_latlon.buffer(TILE_SELECTION_BUFFER_RADIUS_DEGREES))
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
        
#         BUFFER_DEGREES = 0.1
        
        if cell_size is None:
            cell_size = CELL_SIZE_DEGREES

        if buffer_size is None:
            buffer_size = BUFFER_DEGREES

        if target_CRS is None:
            target_CRS = WGS84

        if exists(subset_filename):
            print(f"loading existing {variable_name} subset file: {subset_filename}")

            with rasterio.open(subset_filename, "r") as f:
                subset = f.read(1)
                affine = f.transform

            return subset, affine
        
        print(f"generating {variable_name} subset")

        tiles = select_tiles(ROI_latlon)
        print(f"tiles: {tiles}")
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
            print(f"searching pattern: {pattern}")
            matches = sorted(glob(pattern, recursive=True))
            
            if len(matches) == 0:
                print(f"no files found for tile: {tile}")
                files_found = sorted(glob(join(raster_directory, '**', '*'), recursive=True))
                tiles_found = sorted(set([splitext(basename(filename))[0].split("_")[2] for filename in files_found]))
                print(f"files found: {', '.join(tiles_found)}")
                continue
            
            input_filename = matches[0]
            print(f"{tile}: {input_filename}")

            with rasterio.open(input_filename, "r") as input_file:
                source_CRS = input_file.crs
                input_affine = input_file.transform
                
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
                
                col_min = min(col_ul, col_ll)
                col_min = max(col_min, 0)
                col_max = max(col_ur, col_lr)
                
                row_min = min(row_ul, row_ur)
                row_min = max(row_min, 0)
                row_max = max(row_ll, row_lr)
                
                window = (row_min, row_max), (col_min, col_max)
                
                if row_min < 0 or col_min < 0 or row_max <= row_min or col_max <= col_min:
                    print(f"raster does not intersect target surface: {input_filename}")
                    continue

                window = Window.from_slices(*window)
                source_subset = input_file.read(1, window=window)
                source_affine = window_transform(window, input_affine)

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
        
            print("writing subset: {}".format(subset_filename))
            with rasterio.open(subset_filename, "w", **subset_profile) as input_file:
                input_file.write(output_raster.astype(np.float32), 1)

        return output_raster, target_affine

    def generate_patch(polygon, affine):
        if isinstance(polygon, MultiPolygon):
            polygon = list(polygon)[0]

        polygon_indices = [~affine * coords for coords in polygon.exterior.coords]
        patch = Polygon(polygon_indices, fill=None, color="black", linewidth=1)
        
       
        return patch

    def inventory(source_directory):
        #print(f"searching data: {source_directory}")
        date_directories = sorted(glob(join(source_directory, "*")))
        date_directories = [directory for directory in date_directories if isdir(directory)]
        dates_available = [datetime.strptime(basename(directory), "%Y.%m.%d").date() for directory in date_directories]
        years_available = list(set(sorted([date_step.year for date_step in dates_available])))
        
       
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

       # print(f"year: {year}")

        if exists(stack_filename):
           # print(f"loading stack: {stack_filename}")
            texts(f"loading stack: {stack_filename}\n")

            with h5py.File(stack_filename, "r") as stack_file:
                ET_stack = np.array(stack_file["ET"])
                PET_stack = np.array(stack_file["PET"])
                affine = Affine(*list(stack_file["affine"]))

            return ET_stack, PET_stack, affine

        #print(f"generating stack")

        ET_sparse_stack = None
        ESI_sparse_stack = None

        dates_in_year = [
            date_step
            for date_step
            in dates_available
            if date_step.year == year
        ]

        #print("dates_in_year:")
        #print(dates_in_year)


        if len(dates_in_year) == 0:
            raise ValueError(f"no dates for year: {year}")

        for date_step in dates_in_year:
            #print(f"creation_date: {date_step.strftime('%Y-%m-%d')}")

            if not exists(subset_directory):
                makedirs(subset_directory)

            ET_subset_filename = join(subset_directory, f"{date_step.strftime('%Y.%m.%d')}_{ROI_name}_ET_subset.tif")
            ESI_subset_filename = join(subset_directory, f"{date_step.strftime('%Y.%m.%d')}_{ROI_name}_ESI_subset.tif")

            source_raster_directory = join(source_directory, date_step.strftime("%Y.%m.%d"))

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
                print(e)
                #print(f"problem generating ET subset for creation_date: {date_step.strftime('%Y-%m-%d')}")
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
                print(e)
                #print(f"problem generating ESI subset for creation_date: {date_step.strftime('%Y-%m-%d')}")
                continue

            subset_shape = ESI_subset.shape
            rows, cols = subset_shape
            month = date_step.month
            day = date_step.day

            if ET_sparse_stack is None:
                days_in_year = (datetime(year, 12, 31) - datetime(year, 1, 1)).days + 1
                ET_sparse_stack = np.full((days_in_year, rows, cols), np.nan, dtype=np.float32)

            if ESI_sparse_stack is None:
                days_in_year = (datetime(year, 12, 31) - datetime(year, 1, 1)).days + 1
                ESI_sparse_stack = np.full((days_in_year, rows, cols), np.nan, dtype=np.float32)

            day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days - 1

            ET_doy_image = ET_sparse_stack[day_of_year, :, :]
            ET_sparse_stack[day_of_year, :, :] = np.where(np.isnan(ET_doy_image), ET_subset, ET_doy_image)

            ESI_doy_image = ESI_sparse_stack[day_of_year, :, :]
            ESI_sparse_stack[day_of_year, :, :] = np.where(np.isnan(ESI_doy_image), ESI_subset, ESI_doy_image)

        if ET_sparse_stack is None:
            raise ValueError("no ET stack generated")
            #texts("no ET stack generated\n")

        if ESI_sparse_stack is None:
            raise ValueError("no ESI stack generated")
            #texts("no ESI stack generated\n")

        PET_sparse_stack = ET_sparse_stack / ESI_sparse_stack

        #print(f"interpolating ET stack for year: {year}")
        ET_stack = interpolate_stack(ET_sparse_stack)
        PET_stack = interpolate_stack(PET_sparse_stack)

        stack_directory = dirname(stack_filename)

        if not exists(stack_directory):
            makedirs(stack_directory)

        #print(f"writing stack: {stack_filename}")
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
                f = interp1d(known_days, pixel_timeseries, axis=0, kind="nearest", fill_value="extrapolate")
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
        monthly_means_filename = join(monthly_means_directory, f"{year}_monthly_means.csv")
        

        
        if exists(monthly_means_filename):
            #print(f"loading monthly means: {monthly_means_filename}")
            monthly_means_df = pd.read_csv(monthly_means_filename)
        else:
            days, rows, cols = ET_stack.shape
            subset_shape = (rows, cols)
            #print("rasterizing ROI")
            mask = geometry_mask([ROI_latlon], subset_shape, subset_affine, invert=True)

           # print(f"processing monthly values for year: {year}")
            monthly_means = []

            for j, month in enumerate(range(3, 11)):
                if not exists(monthly_sums_directory):
                    makedirs(monthly_sums_directory)

                ET_monthly_filename = join(monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

                if exists(ET_monthly_filename):
                    #print(f"loading monthly file: {ET_monthly_filename}")
                    with rasterio.open(ET_monthly_filename, "r") as f:
                        ET_monthly = f.read(1)
                else:
                    start = datetime(year, month, 1).date()
                    #print("start creation_date: " + start.strftime("%Y-%m-%d"))
                    start_index = start.timetuple().tm_yday
                    #print(f"start index: {start_index}")
                    end = datetime(year, month + 1, 1).date()
                    #print("end creation_date: " + end.strftime("%Y-%m-%d"))
                    end_index = end.timetuple().tm_yday
                    #print(f"end index: {end_index}")
                    ET_month_stack = ET_stack[start_index:end_index, :, :]
                    ET_monthly = np.nansum(ET_month_stack, axis=0)

                    # plt.imshow(ET_monthly)
                    # plt.colorbar()
                    # plt.title(f"{year:04d}-{month:02d}")
                    # plt.show()

                    #print(f"writing ET monthly file: {ET_monthly_filename}")

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
                    #print(f"loading monthly file: {PET_monthly_filename}")
                    with rasterio.open(PET_monthly_filename, "r") as f:
                        PET_monthly = f.read(1)
                else:
                    start = datetime(year, month, 1).date()
                    #print("start creation_date: " + start.strftime("%Y-%m-%d"))
                    start_index = start.timetuple().tm_yday
                    #print(f"start index: {start_index}")
                    end = datetime(year, month + 1, 1).date()
                    #print("end creation_date: " + end.strftime("%Y-%m-%d"))
                    end_index = end.timetuple().tm_yday
                    #print(f"end index: {end_index}")
                    PET_month_stack = PET_stack[start_index:end_index, :, :]
                    PET_monthly = np.nansum(PET_month_stack, axis=0)

                    # plt.imshow(PET_monthly)
                    # plt.colorbar()
                    # plt.title(f"{year:04d}-{month:02d}")
                    # plt.show()

                    #print(f"writing PET monthly file: {PET_monthly_filename}")

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
                monthly_means.append([year, month, ET_monthly_mean, PET_monthly_mean])

            if not exists(monthly_means_directory):
                makedirs(monthly_means_directory)

            monthly_means_df = pd.DataFrame(monthly_means, columns=["Year", "Month", "ET", "PET"])
            #print(f"writing monthly means: {monthly_means_filename}")
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
        #print(f"roi_mask:")
        #print(roi_mask)
        open_mask = (rasterio.open(subset_directory + "/masked_area.tif"))
        #print(f"open_mask:")
        #print(open_mask)
        area_mask = open_mask.read()
        #print(f"area_mask:")
        #print(area_mask)
        #area = np.count_nonzero((area_mask[0][roi_mask[0]]))
        area = np.count_nonzero(((area_mask[0][roi_mask[0]])) == 0)
        #print(f"area:")
        #print(area)

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
       # print(f"array_list:")
       # print(array_list)
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
        fig.suptitle((f"Evapotranspiration For {ROI_name} - {year} - {ROI_acres} acres"), fontsize = 14)
        grid = plt.GridSpec(3, 4, wspace=0.4, hspace=0.3)

        for i, month in enumerate((3, 4, 5, 6, 7, 8, 9, 10)):
            #print(f"rendering month: {month} sub-figure: {i}")
            subfigure_title = datetime(year, month, 1).date().strftime("%Y-%m")
            #print(f"sub-figure title: {subfigure_title}")
            ET_monthly_filename = join(monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

            if not exists(ET_monthly_filename):
                raise IOError(f"monthly sum file not found: {ET_monthly_filename}")

            #print(f"loading monthly file: {ET_monthly_filename}")
            with rasterio.open(ET_monthly_filename, "r") as f:
                monthly = f.read(1)

            ax = plt.subplot(grid[int(i / 4), i % 4])
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            #print(f"min: {np.nanmin(monthly)} mean: {np.nanmean(monthly)} max: {np.nanmax(monthly)}")

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
        fig.colorbar(im, cax=cbar_ax, ticks=[], label= f'Low                                                            High')

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
        plt.legend(labels=['ET'], loc ='upper right')
        ax.legend(loc='upper left', fontsize=6)
        ax.set(xlabel="Month", ylabel="ET (mm)")
        ymin = min(min(main_df["ET"]), min(main_df["ET"]))
        ymax = max(max(main_df["PET"]), max(main_df["PET"]))
        ylim = (int(ymin), int(ymax + 10))
        ax.set(ylim=ylim)
        ax.set_yticks([int(ymin), int(ymax)+10])
        ax.set_yticklabels(['Low', 'High'])
       

        plt.title(f"Area of Interest Average Monthly Water Use", fontsize = 10)
        caption =  "ET and PET calculated by the PT-JPL retrieval: Fisher et al. (2008) with Landsat data"
        caption2 = f"Visualization created {date}"
        plt.figtext(0.48, 0.001, caption, wrap = True, verticalalignment = 'bottom', horizontalalignment = 'center', fontsize = 5)
        plt.figtext(0.93, 0.001, caption2, wrap = True, verticalalignment = 'bottom', horizontalalignment = 'right', fontsize = 5)
        plt.tight_layout()

        #print(f"writing figure: {figure_filename}")
        texts(f"Figure saved\n")
        end_time = datetime.now().strftime("%H%M")
        texts(f"End Time:{end_time}\n")
        texts("\n")
        plt.savefig(figure_filename, dpi=300)
        #plt.show()
        #plt.close(fig)
        
        add_image(figure_filename)

    def water_rights(
            ROI,
            start,
            end,
            #acres,
            output,
            source_path,
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
        DEFAULT_FIGURE_DIRECTORY = Path(f"{output}/figures")
        DEFAULT_SOURCE_DIRECTORY = Path(f"{source_path}")
        DEFAULT_SUBSET_DIRECTORY = Path(f"{output}/subset/{ROI_base}")
        DEFAULT_NAN_SUBSET_DIRECTORY = Path(f"{output}/nan_subsets/{ROI_base}")
        DEFAULT_MONTHLY_DIRECTORY = Path(f"{output}/monthly/{ROI_base}")
        DEFAULT_STACK_DIRECTORY = Path(f"{output}/stack/{ROI_base}")
        DEFAULT_MONTHLY_NAN_DIRECTORY = Path(f"{output}/monthly_nan/{ROI_base}")
        DEFAULT_MONTHLY_MEANS_DIRECTORY = Path(f"{output}/monthly_means/{ROI_base}")
        
        if ROI_name is None:
            ROI_name = splitext(basename(ROI))[0]

        if working_directory is None:
            working_directory = ROI_name

        if remove_working_directory is None:
            remove_working_directory = True

        if subset_directory is None:
            subset_directory = join(working_directory, DEFAULT_SUBSET_DIRECTORY)

        if nan_subset_directory is None:
            nan_subset_directory = join(working_directory, DEFAULT_NAN_SUBSET_DIRECTORY)

        if monthly_sums_directory is None:
            monthly_sums_directory = join(working_directory, DEFAULT_MONTHLY_DIRECTORY)

        if stack_directory is None:
            stack_directory = join(working_directory, DEFAULT_STACK_DIRECTORY)

        if monthly_means_directory is None:
            monthly_means_directory = join(working_directory, DEFAULT_MONTHLY_MEANS_DIRECTORY)

        if monthly_nan_directory is None:
            monthly_nan_directory = join(working_directory, DEFAULT_MONTHLY_NAN_DIRECTORY)

        if source_directory is None:
            source_directory = DEFAULT_SOURCE_DIRECTORY

        if figure_directory is None:
            figure_directory = DEFAULT_FIGURE_DIRECTORY

        if target_CRS is None:
            target_CRS = WGS84
        
        if start == end :
            str_time = datetime.now().strftime("%H%M")
            texts(f"Start Time:{str_time}\n")
            display_text01 = io.StringIO(f"Generating ET for {ROI_name}:\n{start}\n")
            output01 = display_text01.getvalue()
            text.insert(1.0, output01)
            root.update()
        else:
            str_time = datetime.now().strftime("%H%M")
            texts(f"Start Time:{str_time}\n")
            display_text01 = io.StringIO(f"Generating ET for {ROI_name}:\n{start} - {end}\n")
            output01 = display_text01.getvalue()
            text.insert(1.0, output01)
            root.update()
        
        print(f"ROI name: {ROI_name}")
        print(f"loading ROI: {ROI}")
        ROI_latlon = gpd.read_file(ROI).to_crs(WGS84).geometry[0]
        ROI_for_nan = list((gpd.read_file(ROI).to_crs(WGS84)).geometry)
        ROI_acres = round(ROI_area(ROI, working_directory), 2)

        years_available, dates_available = inventory(source_directory)
        monthly_means = []

        if start == end:
            years_x = [start]
        else:
            years_x = [*range(int(start), int(end)+1)]
        
        for i, year in enumerate(years_x):
            print(f"processing: {year}")
            texts(f"Processing: {year}\n")
        
            
            stack_filename = join(stack_directory, f"{year:04d}_{ROI_name}_stack.h5")

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
                print(e)
                print(f"unable to generate stack for year: {year}")
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
            
            texts("Calculating uncertainty\n")
            
            calculate_percent_nan(
                ROI_for_nan,
                subset_directory,
                nan_subset_directory,
                monthly_nan_directory)
            
            texts("Generating figure\n")
            
            nan_means = []
            nd = pd.read_csv(f"{monthly_nan_directory}/{year}.csv")
            nan_means.append(nd)
            print(f"application nan means: \n {nan_means}")
        
            month_means = []
            mm = pd.read_csv(f"{monthly_means_directory}/{year}_monthly_means.csv")
            month_means.append(mm)
            print(f"application monthly means: \n {month_means}")

            idx =  {'Months': [3,4,5,6,7,8,9,10]}
            df1 = pd.DataFrame(idx, columns = ['Months'])
            df2 = pd.DataFrame(idx, columns = ['Months'])

            main_dfa = pd.merge(left = df1, right = mm, how = 'left', left_on = "Months", right_on = "Month")
            main_df = pd.merge(left = main_dfa, right = nd, how = 'left', left_on = "Months", right_on = "month")
            main_df = main_df.replace(np.nan,100)
            print(f'main_df: {main_df}')
            
            monthly_means_df = pd.concat(month_means, axis=0)
            print("monthly_means_df:")
            mean = np.nanmean(monthly_means_df["ET"])
            sd = np.nanstd(monthly_means_df["ET"])
            vmin = max(mean - 2 * sd, 0)
            vmax = mean + 2 * sd

            today = dt.today()
            date= str(today)

            print(f"generating figure for year: {year}")

            figure_output_directory = join(figure_directory, ROI_name)

            if not exists(figure_output_directory):
                makedirs(figure_output_directory)

            figure_filename = join(figure_output_directory, f"{year}_{ROI_name}.png")

            if exists(figure_filename):
                print(f"figure already exists: {figure_filename}")
                texts(f"figure exists in working directory\n")
                add_image(figure_filename)
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
                print(e)
                print(f"unable to generate figure for year: {year}")
                continue
                

    
    if isfile(ROI) == True:
        water_rights(
        ROI,
        start,
        end,
        #acres,
        output,
        source_path,
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
       
    elif isdir(ROI) == True:
        for items in scandir(ROI):
            if items.name.endswith(".geojson"):
                roi_name = abspath(items)
                water_rights(
                roi_name,
                start,
                end,
                #acres,
                output,
                source_path,
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
        texts("Not a valid file")
        print("Not a valid file")
    
HEIGHT = 600
WIDTH = 700

root =  Tk()
root.title("JPL-NMOSE ET visualizer")
root.geometry("700x600")
root.resizable(0,0)

canvas = Canvas(root, height = HEIGHT, width = WIDTH )
canvas.pack()

myFont = font.Font(family='Helvetica', size = 12)

imgpath = join(dirname(abspath(sys.argv[0])), "img4.png")

# imgpath = "/Users/seamony/Desktop/WR_GUI/img4.png"


if exists(imgpath) == True:
    img = PhotoImage(file = imgpath)
    background_label = Label(root, image = img)
    background_label.place(relwidth = 1, relheight = 1)
    low_frame = Frame(root, bg = 'skyblue', bd = 4)
    low_frame.place(relx = 0.20, rely = 0.5, relwidth = 0.35, relheight = 0.4, anchor = 'n')
    img_frame = Frame(root, bg = 'skyblue', bd = 4)
    img_frame.place(relx = 0.675, rely = 0.5, relwidth = 0.60, relheight = 0.4, anchor = 'n')
else: 
    background_label = Label(root, bg = 'lightseagreen')
    background_label.place(relwidth = 1, relheight = 1)
    low_frame = Frame(root, bg = 'mediumturquoise', bd = 4)
    low_frame.place(relx = 0.20, rely = 0.5, relwidth = 0.35, relheight = 0.4, anchor = 'n')
    img_frame = Frame(root, bg = 'mediumturquoise', bd = 4)
    img_frame.place(relx = 0.675, rely = 0.5, relwidth = 0.60, relheight = 0.4, anchor = 'n')
    

text = scrolledtext.ScrolledText(low_frame, width = 200, height = 200)
text.config(state=NORMAL)
text.pack()

image = Text(img_frame, width = 200, height = 200)
image.config(state=NORMAL)
image.pack()

def texts(sometexts):
    display_text = io.StringIO(f"{sometexts}")
    output = display_text.getvalue()
    text.insert('1.0', output)
    root.update()
    
    return "break"

    
def browse_data(i):
    
    phrase = i
    
    if isdir(phrase) == True:
        landsat_file = filedialog.askdirectory(initialdir = phrase, title ="Select Landsat directory")
        if landsat_file == phrase:
            pass
        elif len(landsat_file) < 1:
            pass
        else:
            clear_data()
            entry_filepath.insert(END, landsat_file )
    else:
        landsat_file = filedialog.askdirectory(initialdir = "C:/Users/", title ="Select Landsat directory")
        if landsat_file == phrase:
            pass
        elif len(landsat_file) < 1:
            pass
        else:
            clear_data()
            entry_filepath.insert(END, landsat_file )
       
        
def browse_roi(i):

    phrase = i
    
    if isdir(phrase) == True:
        roi_file = filedialog.askopenfilename(initialdir = phrase, title ="Select geojson file")
        if roi_file == phrase:
            pass
        elif len(roi_file) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_file)
            
    elif isfile(phrase) == True:
        roi_file = filedialog.askopenfilename(initialdir = phrase, title ="Select geojson file")
        if roi_file == phrase:
            pass
        elif len(roi_file) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_file)
    
    else:
        roi_file = filedialog.askopenfilename(initialdir = "C:/Users/", title ="Select geojson file")
        if roi_file == phrase:
            pass
        elif len(roi_file) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_file)

def browse_batch(i):

    phrase = i
    
    if isdir(phrase) == True:
        roi_batch =  filedialog.askdirectory(initialdir = phrase, title ="Select outpt directory")
        if roi_batch == phrase:
            pass
        elif len(roi_batch) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_batch)
    else:
        roi_batch =  filedialog.askdirectory(initialdir = "C:/Users/", title ="Select outpt directory")
        if roi_batch == phrase:
            pass
        elif len(roi_batch) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_batch)
    
def browse_output(i):
    
    phrase = i
    
    if isdir(phrase) == True:
        output_file =  filedialog.askdirectory(initialdir = phrase, title ="Select outpt directory")
        if output_file == phrase:
            pass
        elif len(output_file) < 1:
            pass
        else:
            clear_output()
            output_path.insert(END, output_file)
    else:
        output_file =  filedialog.askdirectory(initialdir = "C:/Users/", title ="Select outpt directory")
        if output_file == phrase:
            pass
        elif len(output_file) < 1:
            pass
        else:
            clear_output()
            output_path.insert(END, output_file)
    

def clear_roi():    
    entry_roi.delete(0, 'end')

def clear_data():
    entry_filepath.delete(0, 'end')

def clear_output():
    output_path.delete(0, 'end')

def clear_text():
    image.delete(1.0, END)
    text.delete(1.0, END)
    progress.set(0)
    root.update()

def add_image(filepath):
    global im_resize
    print(f"opening image: {filepath}")
    im = PIL.Image.open(filepath)
    im = im.resize((375, 225), PIL.Image.BICUBIC)
    im_resize = PIL.ImageTk.PhotoImage(im)
    image.image_create('1.0',image = im_resize)
    # root.image_panel.see('1.0')
    # root.update()

def get_path(path):
    
    if path == 'Landsat':
        filepath = entry_filepath.get()
    elif path == 'Batch':
        filepath = entry_roi.get()
    elif path == 'Single':
        filepath = entry_roi.get()
    elif path == 'Output':
        filepath = output_path.get()
    else:
        print(f"Error retrieving path(s)")
    
    return filepath

# GEOJSON/ROI FILEPATH
entry_roi = Entry(root, font = 10, bd = 2)
entry_roi.insert(END, "Water Rights Boundary")
#entry_roi.insert(END, "C:/Users/CashOnly/Desktop/PT-JPL/ROI_477/2035.geojson")
entry_roi['font'] = myFont
entry_roi.place(relx = 0.36, rely = 0.1, relwidth = .66, relheight = 0.05, anchor = 'n')

roi_button = Button(root, text = "Single", width = 8, command = lambda:[browse_roi(get_path('Single'))])
roi_button['font'] = myFont
roi_button.place(relx = 0.85, rely = 0.1 , relheight = 0.05)

roi_batch = Button(root, text = "Batch", width = 8, command = lambda:[browse_batch(get_path('Batch'))])
roi_batch['font'] = myFont
roi_batch.place(relx = 0.720, rely = 0.1 , relheight = 0.05)

# LANDSAT DATA FILEPATH
entry_filepath = Entry(root,  font = 10, bd = 2, borderwidth = 2)
entry_filepath.insert(END, 'Landsat Directory')
#entry_filepath.insert(END, 'E:/Personal/ISC_DATA')
entry_filepath['font'] = myFont
entry_filepath.place(relx = 0.41, rely = 0.2, relwidth = .76, relheight = 0.05, anchor = 'n')

filepath_button = Button(root, text = "Search", width  = 10, command = lambda: [ browse_data(get_path('Landsat'))])
filepath_button['font'] = myFont
filepath_button.place(relx = 0.825, rely = 0.2, relheight = 0.05)


# OUTPUT FILEPATH
output_path = Entry(root, font = 10, bd = 2)
output_path.insert(END, "Output Directory")
#output_path.insert(END, "C:/Users/CashOnly/Desktop/PT-JPL")
output_path['font'] = myFont
output_path.place(relx = 0.41, rely = 0.3, relwidth = 0.76, relheight = 0.05, anchor = 'n')

output_button = Button(root,text = "Search", width = 10, command = lambda:[browse_output(get_path('Output'))])
output_button['font'] = myFont
output_button.place(relx = 0.825, rely = 0.3, relheight = 0.05)

# START YEAR
entry_start = Entry(root, font = 10, bd = 2, justify='center')
entry_start['font'] = myFont
entry_start.place(relx = 0.09, rely = 0.4, relwidth = .12, relheight = 0.05, anchor = 'n')
#entry_start.insert(0, "2020")
entry_start.insert(0, "Start")

# END YEAR
entry_end = Entry(root, font = 10, bd = 2, justify='center')
entry_end['font'] = myFont
entry_end.place(relx = 0.24, rely = 0.4, relwidth = 0.12, relheight= 0.05, anchor = 'n')
#entry_end.insert(0, "2020")
entry_end.insert(0, "End")

# # WR AREA
# options = ['Column','Geoanalysis']
# variable = StringVar(root)
# variable.set(options[0])
# entry_area = OptionMenu(root, variable, *options)
# # #entry_area = Entry(root, font = 2, bd = 2, width = 10)
# # entry_area['font'] = myFont
# # entry_area.place(relx = 0.355, rely = 0.4, relwidth = 0.15, relheight = 0.05)
# # #entry_area.insert(0, "Acres")

#Clear Texts
clear_text = Button(root, text = 'Clear Board', width =10, command = clear_text)
clear_text['font'] = myFont
clear_text.place(relx = 0.825, rely=0.4, relheight=0.05)

# SUBMIT BUTTON
submit_button = Button(root, text = "Submit", width = 10, command = submit)
submit_button['font'] = myFont
submit_button.place(relx = 0.670, rely = 0.4, relheight = 0.05)


root.mainloop()


# In[ ]:



