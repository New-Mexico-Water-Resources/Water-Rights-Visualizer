import logging
from datetime import datetime
from os import makedirs
from os.path import splitext, basename, join, exists
from pathlib import Path
from tkinter import Tk, Text
from tkinter.scrolledtext import ScrolledText

import geopandas as gpd
import numpy as np
import pandas as pd

import cl
from .ROI_area import ROI_area
from .calculate_percent_nan import calculate_percent_nan
from .constants import WGS84, START_MONTH, END_MONTH, START_YEAR, END_YEAR
from .data_source import DataSource
from .display_image_tk import display_image_tk
from .display_text_tk import display_text_tk
from .generate_figure import generate_figure
from .generate_stack import generate_stack
from .process_monthly import process_monthly

logger = logging.getLogger(__name__)

def water_rights(
        ROI,
        input_datastore: DataSource,
        output_directory: str,
        start_year: int = START_YEAR,
        end_year: int = END_YEAR,
        start_month: int = START_MONTH,
        end_month: int = END_MONTH,
        ROI_name: str = None,
        figure_directory: str = None,
        working_directory: str = None,
        subset_directory: str = None,
        nan_subset_directory: str = None,
        stack_directory: str = None,
        monthly_sums_directory: str = None,
        monthly_means_directory: str = None,
        monthly_nan_directory: str = None,
        target_CRS: str = None,
        remove_working_directory: bool = True,
        root: Tk = None,
        image_panel: Text = None,
        text_panel: ScrolledText = None):
    ROI_base = splitext(basename(ROI))[0]
    DEFAULT_FIGURE_DIRECTORY = Path(f"{output_directory}/figures")
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

    if figure_directory is None:
        figure_directory = DEFAULT_FIGURE_DIRECTORY

    if target_CRS is None:
        target_CRS = WGS84

    str_time = datetime.now().strftime("%H%M")

    display_text_tk(
        text=f"Start Time:{str_time}\n",
        text_panel=text_panel,
        root=root
    )

    year_range = start_year if start_year == end_year else f"{start_year} - {end_year}"

    display_text_tk(
        text=f"Generating ET for {ROI_name}:\n{year_range}\n",
        text_panel=text_panel,
        root=root
    )

    logger.info(f"ROI name: {ROI_name}")
    logger.info(f"loading ROI: {ROI}")
    ROI_latlon = gpd.read_file(ROI).to_crs(WGS84).geometry[0]
    ROI_for_nan = list((gpd.read_file(ROI).to_crs(WGS84)).geometry)
    ROI_acres = round(ROI_area(ROI, working_directory), 2)

    years_available, dates_available = input_datastore.inventory()
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
        logger.info(f"processing year {cl.time(year)} at ROI {cl.name(ROI_name)}")
        message = f"processing: {year}"

        display_text_tk(
            text="{message}\n",
            text_panel=text_panel,
            root=root
        )

        stack_filename = join(stack_directory, f"{year:04d}_{ROI_name}_stack.h5")

        try:
            display_text_tk(
                text=f"loading stack: {stack_filename}\n",
                text_panel=text_panel,
                root=root
            )

            ET_stack, PET_stack, affine = generate_stack(
                ROI_name=ROI_name,
                ROI_latlon=ROI_latlon,
                year=year,
                ROI_acres=ROI_acres,
                input_datastore=input_datastore,
                subset_directory=subset_directory,
                dates_available=dates_available,
                stack_filename=stack_filename,
                target_CRS=target_CRS
            )
        except Exception as e:
            logger.exception(e)
            logger.warning(f"unable to generate stack for year {cl.time(year)} at ROI {cl.name(ROI_name)}")

            continue

        monthly_means_df = process_monthly(
            ET_stack=ET_stack,
            PET_stack=PET_stack,
            ROI_latlon=ROI_latlon,
            ROI_name=ROI_name,
            subset_affine=affine,
            CRS=target_CRS,
            year=year,
            monthly_sums_directory=monthly_sums_directory,
            monthly_means_directory=monthly_means_directory
        )

        monthly_means.append(monthly_means_df)

        display_text_tk(
            text="Calculating uncertainty\n",
            text_panel=text_panel,
            root=root
        )

        calculate_percent_nan(
            ROI_for_nan,
            subset_directory,
            nan_subset_directory,
            monthly_nan_directory
        )

        display_text_tk(
            text="Generating figure\n",
            text_panel=text_panel,
            root=root
        )

        nan_means = []
        nd = pd.read_csv(f"{monthly_nan_directory}/{year}.csv")
        nan_means.append(nd)
        # logger.info(f"application nan means: \n {nan_means}")

        month_means = []
        mm = pd.read_csv(f"{monthly_means_directory}/{year}_monthly_means.csv")
        month_means.append(mm)
        # logger.info(f"application monthly means: \n {month_means}")

        idx = {'Months': range(start_month, end_month + 1)}
        df1 = pd.DataFrame(idx, columns=['Months'])
        df2 = pd.DataFrame(idx, columns=['Months'])

        main_dfa = pd.merge(left=df1, right=mm, how='left', left_on="Months", right_on="Month")
        main_df = pd.merge(left=main_dfa, right=nd, how='left', left_on="Months", right_on="month")
        main_df = main_df.replace(np.nan, 100)
        # logger.info(f'main_df: {main_df}')
        monthly_means_df = pd.concat(month_means, axis=0)
        # logger.info("monthly_means_df:")
        mean = np.nanmean(monthly_means_df["ET"])
        sd = np.nanstd(monthly_means_df["ET"])
        vmin = max(mean - 2 * sd, 0)
        vmax = mean + 2 * sd

        today = datetime.today()
        date = str(today)

        logger.info(f"generating figure for year {cl.time(year)} ROI {cl.place(ROI_name)}")

        figure_output_directory = join(figure_directory, ROI_name)

        if not exists(figure_output_directory):
            makedirs(figure_output_directory)

        figure_filename = join(figure_output_directory, f"{year}_{ROI_name}.png")

        if exists(figure_filename):
            logger.info(f"figure already exists: {cl.file(figure_filename)}")

            display_text_tk(
                text=f"figure exists in working directory\n",
                text_panel=text_panel,
                root=root
            )

            display_image_tk(
                filename=figure_filename,
                image_panel=image_panel
            )

            continue

        # print("main_df")
        # print(main_df)

        try:
            generate_figure(
                ROI_name=ROI_name,
                ROI_latlon=ROI_latlon,
                ROI_acres=ROI_acres,
                creation_date=today,
                year=year,
                vmin=vmin,
                vmax=vmax,
                affine=affine,
                main_df=main_df,
                monthly_sums_directory=monthly_sums_directory,
                figure_filename=figure_filename,
                start_month=start_month,
                end_month=end_month,
                root=root,
                text_panel=text_panel,
                image_panel=image_panel
            )
        except Exception as e:
            logger.exception(e)
            logger.info(f"unable to generate figure for year: {year}")

            continue
