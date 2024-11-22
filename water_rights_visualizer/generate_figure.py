from datetime import datetime, date
from logging import getLogger
from os.path import join, exists, dirname
from os import makedirs
from tkinter import Text, Tk
from tkinter.scrolledtext import ScrolledText

import matplotlib.pyplot as plt
import calendar
import pandas as pd
import rasterio
import seaborn as sns
from affine import Affine
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Polygon
import numpy as np

from .constants import START_MONTH, END_MONTH
from .display_image_tk import display_image_tk

# from .display_text_tk import display_text_tk
from .generate_patch import generate_patch

from .write_status import write_status
from .variable_types import get_available_variable_source_for_date, OPENET_TRANSITION_DATE

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

    max_length_short = 15
    max_length_medium = 30
    title_fontsize = 14

    if len(ROI_name) <= max_length_short:
        title = f"Evaotranspiration For {ROI_name}\nYear: {year}, Area: {ROI_acres} acres"
    elif len(ROI_name) <= max_length_medium:
        title_fontsize = 12
        title = f"Evaotranspiration For {ROI_name}\nYear: {year}, Area: {ROI_acres} acres"
    else:
        title_fontsize = 12
        short_name = ROI_name[:max_length_medium] + "..."
        title = f"Evaotranspiration For {short_name}\nYear: {year}, Area: {ROI_acres} acres"

    # Add the title
    fig.suptitle(title, fontsize=title_fontsize)

    n_months = end_month - start_month + 1
    grid_cols = int(n_months / 2)

    grid = plt.GridSpec(3, grid_cols, wspace=0.4, hspace=0.3)

    # Generate sub-figures for each month
    for i, month in enumerate(range(start_month, end_month + 1)):
        logger.info(f"rendering month: {month} sub-figure: {i}")
        # subfigure_title = datetime(year, month, 1).date().strftime("%Y-%m")
        subfigure_title = calendar.month_abbr[month]
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
    fig.subplots_adjust(right=0.78)

    top_y = grid[0, 0].get_position(fig).y1 - 0.05
    bottom_y = grid[1, 0].get_position(fig).y0 + 0.05
    cbar_height = top_y - bottom_y
    cbar_ax = fig.add_axes([0.85, bottom_y, 0.05, cbar_height])
    # cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
    # cbar_ax = fig.add_axes(
    #     [0.85, grid[0, 0].get_position(fig).y1, 0.05, grid[1, 0].get_position(fig).y0 - grid[0, 0].get_position(fig).y1]
    # )
    # fig.colorbar(im, cax=cbar_ax, ticks=[], label=f'Low                                                            High')
    cbar = fig.colorbar(
        im,
        cax=cbar_ax,
        ticks=[],
        # label=f"{round(vmin)} mm                                                      {round(vmax)} mm",
    )

    # Add the min and max labels without rotation
    cbar.ax.text(
        0.5,
        -0.03,
        f"{round(vmin)} mm",  # Bottom label for min value
        transform=cbar.ax.transAxes,
        ha="center",
        va="top",
        fontsize=10,
    )
    cbar.ax.text(
        0.5,
        1.03,
        f"{round(vmax)} mm",  # Top label for max value
        transform=cbar.ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
    )

    # Create a subplot for the main data
    # ax = plt.subplot(grid[2, :])
    # Get the positions for alignment
    left_x = grid[0, 0].get_position(fig).x0  # Left boundary of the grid
    right_x = cbar_ax.get_position(fig).x1  # Right boundary of the colorbar
    bottom_y = grid[2, :].get_position(fig).y0  # Bottom boundary of the grid
    top_y = grid[2, :].get_position(fig).y1  # Top boundary of the grid

    # Add the bottom chart axis, spanning the full width to align with the colorbar
    ax = fig.add_axes([left_x, bottom_y, right_x - left_x, top_y - bottom_y])

    df = main_df[main_df["Year"] == year]
    # df = main_df[df["month" == month]]
    # print(df)
    x = df["Month"]
    # print(f"x (month): {x}")
    y = df["PET"]
    # print(f"y (PET): {y}")
    y2 = df["ET"]
    # print(f"y2 (ET): {y2}")

    # Data before 2008 is just Landsat PTJPL and doesnt have OpenET MIN/MAX bands so use percent_nan to calculate CI
    # ci_pet = df["percent_nan"] / 100 * y
    # pet_ci_ymin = y - ci_pet
    # pet_ci_ymax = y + ci_pet

    # ci_et = df["percent_nan"] / 100 * y2
    # et_ci_ymin = y - ci_et
    # et_ci_ymax = y + ci_et

    # Create a new column for the confidence interval min max that uses the above approach for data before 2008 and just uses ET_MIN and ET_MAX for data after 2008
    # OPENET_TRANSITION_DATE = 2008
    df["pet_ci_ymin"] = df.apply(
        lambda row: (
            row["y"] - (row["percent_nan"] / 100 * row["y"]) if row["year"] < OPENET_TRANSITION_DATE else row["avg_min"]
        ),
        axis=1,
    )
    df["pet_ci_ymax"] = df.apply(
        lambda row: (
            row["y"] + (row["percent_nan"] / 100 * row["y"]) if row["year"] < OPENET_TRANSITION_DATE else row["avg_max"]
        ),
        axis=1,
    )

    df["et_ci_ymin"] = df.apply(
        lambda row: (
            row["y2"] - (row["percent_nan"] / 100 * row["y2"]) if row["year"] < OPENET_TRANSITION_DATE else row["avg_min"]
        ),
        axis=1,
    )
    df["et_ci_ymax"] = df.apply(
        lambda row: (
            row["y2"] + (row["percent_nan"] / 100 * row["y2"]) if row["year"] < OPENET_TRANSITION_DATE else row["avg_max"]
        ),
        axis=1,
    )

    # print(f"ci (nan%): {ci}")
    sns.lineplot(x=x, y=y, ax=ax, color="blue", label="PET")
    sns.lineplot(x=x, y=y2, ax=ax, color="green", label="ET")
    ax.fill_between(x, df["pet_ci_ymin"], df["pet_ci_ymax"], color="b", alpha=0.1)
    ax.fill_between(x, df["et_ci_ymin"], df["et_ci_ymax"], color="g", alpha=0.1)
    plt.legend(labels=["ET"], loc="upper right")
    ax.legend(loc="upper left", fontsize=6)
    # ax.set(xlabel="Month", ylabel="ET (mm)")
    ax.set(xlabel="Month", ylabel="")
    ymin = min(min(main_df["ET"]), min(main_df["ET"]), min(df["pet_ci_ymin"]), min(df["et_ci_ymin"]))
    ymax = max(max(main_df["PET"]), max(main_df["PET"]), max(df["pet_ci_ymax"]), max(df["et_ci_ymax"]))
    ylim = (int(ymin), int(ymax + 10))

    # df["normalized_nan"] = (df["percent_nan"] / 100) * (ymax - ymin) + ymin
    # normalized_min = df["percent_nan"].min()
    # normalized_max = df["percent_nan"].max()
    # df["normalized_nan"] = (df["percent_nan"] - normalized_min) / (normalized_max - normalized_min) * (ymax - ymin) + ymin
    normalized_min = 0
    normalized_max = 100
    df["normalized_nan"] = (df["percent_nan"] - normalized_min) / (normalized_max - normalized_min) * (ymax - ymin) + ymin

    # ax.bar(
    #     x=df["month"],  # Assuming `x` corresponds to months as integers (1–12)
    #     height=df["normalized_nan"],
    #     width=0.8,
    #     color="gray",
    #     alpha=0.3,
    #     label="Cloud Coverage",
    #     zorder=1,  # Ensure bars are plotted behind lines
    # )
    ax2 = ax.twinx()
    bars = ax2.bar(
        x=df["month"],  # Assuming `x` corresponds to months as integers (1–12)
        height=df["normalized_nan"],
        width=0.8,
        color="gray",
        alpha=0.3,
        label="Cloud Coverage",
        zorder=1,  # Ensure bars are plotted behind lines
    )

    # Adjust the secondary y-axis range to match the normalization
    # ax2.set_ylim(ymin, ymax)  # Align with the primary y-axis range
    normalized_ticks = np.linspace(normalized_min, normalized_max, 6)  # Create 6 evenly spaced ticks
    ax2.set_yticks(
        [(tick - normalized_min) / (normalized_max - normalized_min) * (ymax - ymin) + ymin for tick in normalized_ticks]
    )
    ax2.set_yticklabels([f"{int(tick)}%" for tick in normalized_ticks])  # Label them with the original percent values
    ax2.tick_params(axis="y", labelsize=6)

    legend_labels = ["Cloud Cov."]
    legend_colors = ["gray"]
    custom_lines = [plt.Line2D([0], [0], color=legend_colors[i], lw=2, alpha=0.8) for i in range(len(legend_labels))]
    ax2.legend(custom_lines, legend_labels, loc="upper right", fontsize=6)

    ax.set(ylim=ylim)
    ax.set_yticks([int(ymin), int(ymax) + 10])
    # ax.set_yticklabels(['Low', 'High'])
    ax.set_yticklabels([f"{int(ymin)} mm", f"{int(ymax) + 10} mm"])
    ax.tick_params(axis="y", labelsize=6)

    # Set monthly x-axis ticks
    # Set x-axis ticks and labels
    ax.set_xticks(range(1, 13))  # Set ticks for each month (1–12)
    ax.set_xticklabels([calendar.month_abbr[i] for i in range(1, 13)])  # Display month abbreviations (Jan, Feb, ...)

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

    # Close the figure
    plt.close(fig)

    # Display the generated figure in the image panel
    display_image_tk(filename=figure_filename, image_panel=image_panel)

    logger.info("finished generating figure")
