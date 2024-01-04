import io
from datetime import datetime, date
from os import makedirs
from os.path import splitext, basename, join, exists
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import logging

from .constants import WGS84
from .ROI_area import ROI_area
from .process_monthly import process_monthly
from .generate_figure import generate_figure
from .calculate_percent_nan import calculate_percent_nan
from .generate_stack import generate_stack
from .inventory import inventory

logger = logging.getLogger(__name__)

def water_rights(texts, text, root, add_image,
                 ROI,
                 start,
                 end,
                 # acres,
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

    if start == end:
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

    logger.info(f"ROI name: {ROI_name}")
    logger.info(f"loading ROI: {ROI}")
    ROI_latlon = gpd.read_file(ROI).to_crs(WGS84).geometry[0]
    ROI_for_nan = list((gpd.read_file(ROI).to_crs(WGS84)).geometry)
    ROI_acres = round(ROI_area(ROI, working_directory), 2)

    years_available, dates_available = inventory(source_directory)
    monthly_means = []

    if start == end:
        years_x = [start]
    else:
        years_x = [*range(int(start), int(end) + 1)]

    for i, year in enumerate(years_x):
        logger.info(f"processing: {year}")
        texts(f"Processing: {year}\n")

        stack_filename = join(stack_directory, f"{year:04d}_{ROI_name}_stack.h5")

        try:
            texts(f"loading stack: {stack_filename}\n")
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
            logger.exception(e)
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
        logger.info(f"application nan means: \n {nan_means}")

        month_means = []
        mm = pd.read_csv(f"{monthly_means_directory}/{year}_monthly_means.csv")
        month_means.append(mm)
        logger.info(f"application monthly means: \n {month_means}")

        idx = {'Months': [3, 4, 5, 6, 7, 8, 9, 10]}
        df1 = pd.DataFrame(idx, columns=['Months'])
        df2 = pd.DataFrame(idx, columns=['Months'])

        main_dfa = pd.merge(left=df1, right=mm, how='left', left_on="Months", right_on="Month")
        main_df = pd.merge(left=main_dfa, right=nd, how='left', left_on="Months", right_on="month")
        main_df = main_df.replace(np.nan, 100)
        logger.info(f'main_df: {main_df}')

        monthly_means_df = pd.concat(month_means, axis=0)
        logger.info("monthly_means_df:")
        mean = np.nanmean(monthly_means_df["ET"])
        sd = np.nanstd(monthly_means_df["ET"])
        vmin = max(mean - 2 * sd, 0)
        vmax = mean + 2 * sd

        today = str(date.today())
        # creation_date= str(today)

        logger.info(f"generating figure for year: {year}")

        figure_output_directory = join(figure_directory, ROI_name)

        if not exists(figure_output_directory):
            makedirs(figure_output_directory)

        figure_filename = join(figure_output_directory, f"{year}_{ROI_name}.png")

        if exists(figure_filename):
            logger.info(f"figure already exists: {figure_filename}")
            texts(f"figure exists in working directory\n")
            add_image(figure_filename)
            continue

        try:
            generate_figure(
                ROI_name=ROI_name,
                ROI_latlon=ROI_latlon,
                ROI_acres=ROI_latlon,
                creation_date=today,
                year=year,
                vmin=vmin,
                vmax=vmax,
                affine=affine,
                main_df=main_df,
                monthly_sums_directory=monthly_sums_directory,
                figure_filename=figure_filename,
                texts=texts,
                add_image=add_image
            )
        except Exception as e:
            logger.exception(e)
            logger.info(f"unable to generate figure for year: {year}")
            continue