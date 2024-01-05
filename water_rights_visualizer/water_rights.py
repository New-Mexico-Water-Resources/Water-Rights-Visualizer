import io
from datetime import datetime, date
from os import makedirs
from os.path import splitext, basename, join, exists
from pathlib import Path
from tkinter import Tk, Text
from tkinter.scrolledtext import ScrolledText

import numpy as np
import pandas as pd
import geopandas as gpd
import logging

from .constants import WGS84, START_MONTH, END_MONTH
from .ROI_area import ROI_area
from .process_monthly import process_monthly
from .generate_figure import generate_figure
from .calculate_percent_nan import calculate_percent_nan
from .generate_stack import generate_stack
from .inventory import inventory
from .display_image_tk import display_image_tk
from .display_text_tk import display_text_tk

logger = logging.getLogger(__name__)

def water_rights(
        ROI,
        start,
        end,
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
        remove_working_directory=None,
        start_month=START_MONTH,
        end_month=END_MONTH,
        root: Tk = None,
        text_panel: ScrolledText = None,
        image_panel: Text = None):
    """
    Process water rights data for a given region of interest (ROI).

    Args:
        ROI (str): Path to the region of interest shapefile.
        start (str): Start date of the water rights data in the format 'YYYY-MM-DD'.
        end (str): End date of the water rights data in the format 'YYYY-MM-DD'.
        output (str): Path to the output directory.
        source_path (str): Path to the directory containing the water rights data.
        ROI_name (str, optional): Name of the region of interest. Defaults to None.
        source_directory (str, optional): Path to the directory containing the water rights data. 
            Defaults to None.
        figure_directory (str, optional): Path to the directory to save figures. Defaults to None.
        working_directory (str, optional): Path to the working directory. Defaults to None.
        subset_directory (str, optional): Path to the directory to save subset data. Defaults to None.
        nan_subset_directory (str, optional): Path to the directory to save subset data with NaN values. 
            Defaults to None.
        stack_directory (str, optional): Path to the directory to save stacked data. Defaults to None.
        reference_directory (str, optional): Path to the directory containing reference data. 
            Defaults to None.
        monthly_sums_directory (str, optional): Path to the directory to save monthly sums data. 
            Defaults to None.
        monthly_means_directory (str, optional): Path to the directory to save monthly means data. 
            Defaults to None.
        monthly_nan_directory (str, optional): Path to the directory to save monthly data with NaN values. 
            Defaults to None.
        target_CRS (str, optional): Target coordinate reference system (CRS) for the output data. 
            Defaults to None.
        remove_working_directory (str, optional): Path to the directory to remove after processing. 
            Defaults to None.
        start_month (int, optional): Start month of the water rights data. Defaults to START_MONTH.
        end_month (int, optional): End month of the water rights data. Defaults to END_MONTH.
        root (Tk, optional): Root window of the GUI application. Defaults to None.
        text_panel (ScrolledText, optional): Text panel widget of the GUI application. Defaults to None.
        image_panel (Text, optional): Image panel widget of the GUI application. Defaults to None.

    Returns:
        None
    """
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

        display_text_tk(
            text=f"Start Time:{str_time}\n",
            text_panel=text_panel,
            root=root
        )

        display_text01 = io.StringIO(f"Generating ET for {ROI_name}:\n{start}\n")
        output01 = display_text01.getvalue()
        text_panel.insert(1.0, output01)
        root.update()
    else:
        str_time = datetime.now().strftime("%H%M")

        display_text_tk(
            text=f"Start Time:{str_time}\n",
            text_panel=text_panel,
            root=root
        )

        display_text01 = io.StringIO(f"Generating ET for {ROI_name}:\n{start} - {end}\n")
        output01 = display_text01.getvalue()
        text_panel.insert(1.0, output01)
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
        message = f"processing: {year}"
        logger.info(message)

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
        logger.info(f"application nan means: \n {nan_means}")

        month_means = []
        mm = pd.read_csv(f"{monthly_means_directory}/{year}_monthly_means.csv")
        month_means.append(mm)
        logger.info(f"application monthly means: \n {month_means}")

        idx = {'Months': range(start_month, end_month + 1)}
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
        logger.info(f"generating figure for year: {year}")
        figure_output_directory = join(figure_directory, ROI_name)

        if not exists(figure_output_directory):
            makedirs(figure_output_directory)

        figure_filename = join(figure_output_directory, f"{year}_{ROI_name}.png")

        if exists(figure_filename):
            logger.info(f"figure already exists: {figure_filename}")

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
