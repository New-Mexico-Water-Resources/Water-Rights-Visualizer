from datetime import datetime, date
from logging import getLogger
from os.path import join, exists, dirname
from os import makedirs
from tkinter import Text, Tk
from tkinter.scrolledtext import ScrolledText

import matplotlib.pyplot as plt
import pandas as pd
import rasterio
import seaborn as sns
from affine import Affine
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Polygon

from .constants import START_MONTH, END_MONTH
from .display_image_tk import display_image_tk

# from .display_text_tk import display_text_tk
from .generate_patch import generate_patch

from .write_status import write_status
from .variable_types import get_available_variable_source_for_date

logger = getLogger(__name__)


def generate_figure(
    ROI_name: str,
    ROI_latlon: Polygon,
    ROI_acres: float,
    creation_date: date,
    year: int,
    vmin: float,
    vmax: float,
    affine: Affine,
    main_df: pd.DataFrame,
    monthly_sums_directory: str,
    figure_filename: str,
    start_month: int = START_MONTH,
    end_month: int = END_MONTH,
    root: Tk = None,
    text_panel: ScrolledText = None,
    image_panel: Text = None,
    status_filename: str = None,
):
    """
    Generate a figure displaying evapotranspiration data for a specific region of interest (ROI).

    Args:
        ROI_name (str): Name of the region of interest.
        ROI_latlon (Polygon): Polygon representing the region of interest.
        ROI_acres (float): Area of the region of interest in acres.
        creation_date (date): Date of figure creation.
        year (int): Year for which the evapotranspiration data is generated.
        vmin (float): Minimum value for the color scale of the evapotranspiration data.
        vmax (float): Maximum value for the color scale of the evapotranspiration data.
        affine (Affine): Affine transformation for mapping coordinates to pixels.
        main_df (pd.DataFrame): DataFrame containing the main data for generating the figure.
        monthly_sums_directory (str): Directory path for the monthly sums data.
        figure_filename (str): Filename for saving the generated figure.
        start_month (int, optional): Starting month for the data. Defaults to START_MONTH.
        end_month (int, optional): Ending month for the data. Defaults to END_MONTH.
        root (Tk, optional): Root Tkinter window. Defaults to None.
        text_panel (ScrolledText, optional): Text panel for displaying messages. Defaults to None.
        image_panel (Text, optional): Image panel for displaying the generated figure. Defaults to None.
    """

    # Create a new figure
    fig = plt.figure()
    # print(f"ROI name: {ROI_name}")
    # print(f"year: {year}")
    # print(f"ROI_acres: {ROI_acres}")
    fig.suptitle((f"Evapotranspiration For {ROI_name} - {year} - {ROI_acres} acres"), fontsize=14)

    n_months = end_month - start_month + 1
    grid_cols = int(n_months / 2)

    grid = plt.GridSpec(3, grid_cols, wspace=0.4, hspace=0.3)

    # Generate sub-figures for each month
    for i, month in enumerate(range(start_month, end_month + 1)):
        logger.info(f"rendering month: {month} sub-figure: {i}")
        subfigure_title = datetime(year, month, 1).date().strftime("%Y-%m")
        logger.info(f"sub-figure title: {subfigure_title}")
        ET_monthly_filename = join(monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

        # Check if the monthly sum file exists
        if not exists(ET_monthly_filename):
            raise IOError(f"monthly sum file not found: {ET_monthly_filename}")

        # Read the monthly sum data from the file
        with rasterio.open(ET_monthly_filename, "r") as f:
            monthly = f.read(1)

        # Create a subplot for the current month
        ax = plt.subplot(grid[int(i / grid_cols), i % grid_cols])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)

        # Define the colors for the evapotranspiration data
        ET_COLORS = ["#f6e8c3", "#d8b365", "#99974a", "#53792d", "#6bdfd2", "#1839c5"]

        # Create a colormap for the evapotranspiration data
        cmap = LinearSegmentedColormap.from_list("ET", ET_COLORS)
        im = ax.imshow(monthly, vmin=vmin, vmax=vmax, cmap=cmap)
        ax.add_patch(generate_patch(ROI_latlon, affine))
        ax.set_title(subfigure_title)

    # Adjust the layout of the figure
    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    # fig.colorbar(im, cax=cbar_ax, ticks=[], label=f'Low                                                            High')
    fig.colorbar(
        im,
        cax=cbar_ax,
        ticks=[],
        label=f"{round(vmin)} mm                                                      {round(vmax)} mm",
    )

    # Create a subplot for the main data
    ax = plt.subplot(grid[2, :])
    df = main_df[main_df["Year"] == year]
    # df = main_df[df["month" == month]]
    # print(df)
    x = df["Month"]
    # print(f"x (month): {x}")
    y = df["PET"]
    # print(f"y (PET): {y}")
    y2 = df["ET"]
    # print(f"y2 (ET): {y2}")
    ci_pet = df["percent_nan"] / 100 * y
    ci_et = df["percent_nan"] / 100 * y2
    # print(f"ci (nan%): {ci}")
    sns.lineplot(x=x, y=y, ax=ax, color="blue", label="PET")
    sns.lineplot(x=x, y=y2, ax=ax, color="green", label="ET")
    ax.fill_between(x, (y - ci_pet), (y + ci_pet), color="b", alpha=0.1)
    ax.fill_between(x, (y2 - ci_et), (y2 + ci_et), color="g", alpha=0.1)
    plt.legend(labels=["ET"], loc="upper right")
    ax.legend(loc="upper left", fontsize=6)
    # ax.set(xlabel="Month", ylabel="ET (mm)")
    ax.set(xlabel="Month", ylabel="")
    ymin = min(min(main_df["ET"]), min(main_df["ET"]))
    ymax = max(max(main_df["PET"]), max(main_df["PET"]))
    ylim = (int(ymin), int(ymax + 10))
    ax.set(ylim=ylim)
    ax.set_yticks([int(ymin), int(ymax) + 10])
    # ax.set_yticklabels(['Low', 'High'])
    ax.set_yticklabels([f"{int(ymin)} mm", f"{int(ymax) + 10} mm"])

    # Set the title and captions for the figure
    plt.title(f"Area of Interest Average Monthly Water Use", fontsize=10)

    start_date = datetime(year, start_month, 1).date()
    available_et = get_available_variable_source_for_date("ET", start_date)
    if available_et and available_et.file_prefix == "OPENET_ENSEMBLE_":
        caption = f"ET and PET (ETo) calculated from Landsat with the OpenET Ensemble (Melton et al. 2021) the Idaho EPSCOR GRIDMET (Abatzoglou 2012) models, created {creation_date.date()}"
    else:
        caption = f"ET and PET calculated from Landsat with PT-JPL (Fisher et al. 2008), created {creation_date.date()}"
    # caption2 = f"Visualization created {creation_date}"
    plt.figtext(0.48, 0.001, caption, wrap=True, verticalalignment="bottom", horizontalalignment="center", fontsize=5)
    # plt.figtext(0.93, 0.001, caption2, wrap=True, verticalalignment='bottom', horizontalalignment='right', fontsize=5)
    plt.tight_layout()

    end_time = datetime.now().strftime("%H%M")

    write_status(
        message=f"generate_figure end time:{end_time}\n",
        status_filename=status_filename,
        text_panel=text_panel,
        root=root,
    )

    # check to make sure the subdir exists first before writing the file(think matlab savfig does not create it?)
    subdir = dirname(figure_filename)
    if not exists(subdir):
        write_status(
            message=f"Creating subdir {subdir}\n", status_filename=status_filename, text_panel=text_panel, root=root
        )
        makedirs(subdir)

    # Display messages in the text panel
    write_status(
        message=f"Saving figure to {figure_filename}\n",
        status_filename=status_filename,
        text_panel=text_panel,
        root=root,
    )

    # Save the figure to a file
    plt.savefig(figure_filename, dpi=300)

    # Display the generated figure in the image panel
    display_image_tk(filename=figure_filename, image_panel=image_panel)

    logger.info("finished generating figure")
