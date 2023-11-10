from os.path import join, exists
from datetime import datetime, date
from typing import Callable
import pandas as pd
from affine import Affine
from shapely.geometry import Polygon
import rasterio
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from logging import getLogger

from .generate_patch import generate_patch

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
        texts: Callable = lambda: None,
        add_image: Callable = lambda: None):
    
    fig = plt.figure()
    fig.suptitle((f"Evapotranspiration For {ROI_name} - {year} - {ROI_acres} acres"), fontsize = 14)
    grid = plt.GridSpec(3, 4, wspace=0.4, hspace=0.3)

    for i, month in enumerate((3, 4, 5, 6, 7, 8, 9, 10)):
        logger.info(f"rendering month: {month} sub-figure: {i}")
        subfigure_title = datetime(year, month, 1).date().strftime("%Y-%m")
        logger.info(f"sub-figure title: {subfigure_title}")
        ET_monthly_filename = join(monthly_sums_directory, f"{year:04d}_{month:02d}_{ROI_name}_ET_monthly_sum.tif")

        if not exists(ET_monthly_filename):
            raise IOError(f"monthly sum file not found: {ET_monthly_filename}")

        with rasterio.open(ET_monthly_filename, "r") as f:
            monthly = f.read(1)

        ax = plt.subplot(grid[int(i / 4), i % 4])
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        
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
    caption2 = f"Visualization created {creation_date}"
    plt.figtext(0.48, 0.001, caption, wrap = True, verticalalignment = 'bottom', horizontalalignment = 'center', fontsize = 5)
    plt.figtext(0.93, 0.001, caption2, wrap = True, verticalalignment = 'bottom', horizontalalignment = 'right', fontsize = 5)
    plt.tight_layout()

    texts(f"Figure saved\n")
    end_time = datetime.now().strftime("%H%M")
    texts(f"End Time:{end_time}\n")
    texts("\n")
    plt.savefig(figure_filename, dpi=300)
    
    add_image(figure_filename)
