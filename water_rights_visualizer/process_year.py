import sys
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
from .file_path_source import FilepathSource
from .ROI_area import ROI_area
from .calculate_percent_nan import calculate_percent_nan
from .constants import WGS84, START_MONTH, END_MONTH, START_YEAR, END_YEAR
from .data_source import DataSource
from .display_image_tk import display_image_tk
# from .display_text_tk import display_text_tk
from .generate_figure import generate_figure
from .generate_stack import generate_stack
from .process_monthly import process_monthly
from .write_status import write_status

logger = logging.getLogger(__name__)

def process_year(
        year: int,
        dates_available,
        ROI,
        ROI_latlon,
        ROI_acres,
        ROI_for_nan,
        input_datastore: DataSource = None,
        output_directory: str = None,
        start_year: int = START_YEAR,
        end_year: int = END_YEAR,
        start_month: int = START_MONTH,
        end_month: int = END_MONTH,
        ROI_name: str = None,
        input_directory: str = None,
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
        text_panel: ScrolledText = None,
        status_filename: str = None,
        debug: bool = False):
    logger.info(f"processing year {cl.time(year)} at ROI {cl.name(ROI_name)}")
    message = f"processing: {year}"

    write_status(
        message="{message}\n",
        status_filename=status_filename,
        text_panel=text_panel,
        root=root
    )

    stack_filename = join(stack_directory, f"{year:04d}_{ROI_name}_stack.h5")

    try:
        write_status(
            message==f"loading stack: {stack_filename}\n",
            status_filename=status_filename,
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

        if debug:
            sys.exit(1)

        return None

    monthly_means_df = process_monthly(
        ET_stack=ET_stack,
        PET_stack=PET_stack,
        ROI_latlon=ROI_latlon,
        ROI_name=ROI_name,
        subset_affine=affine,
        CRS=target_CRS,
        year=year,
        start_month=start_month,
        end_month=end_month,
        monthly_sums_directory=monthly_sums_directory,
        monthly_means_directory=monthly_means_directory
    )

    # monthly_means.append(monthly_means_df)

    write_status(
        message="Calculating uncertainty\n",
        status_filename=status_filename,
        text_panel=text_panel,
        root=root
    )

    calculate_percent_nan(
        ROI_for_nan,
        subset_directory,
        nan_subset_directory,
        monthly_nan_directory
    )

    write_status(
        message=="Generating figure\n",
        status_filename=status_filename,
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

    figure_filename = join(figure_directory, f"{year}_{ROI_name}.png")

    if exists(figure_filename):
        logger.info(f"figure already exists: {cl.file(figure_filename)}")

        write_status(
            message=f"figure exists in working directory\n",
            status_filename=status_filename,
            text_panel=text_panel,
            root=root
        )

        display_image_tk(
            filename=figure_filename,
            image_panel=image_panel
        )

        # continue
    else:
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
                image_panel=image_panel,
                status_filename=status_filename
            )
        except Exception as e:
            logger.exception(e)
            logger.info(f"unable to generate figure for year: {year}")

            if debug:
                sys.exit(1)

        # continue

    # FIXME delete the stack file

    logger.info(f"finished processing year {year}")
    return monthly_means_df