import logging
from os import chdir, scandir
from os.path import splitext, basename, isfile, isdir, abspath
from pathlib import Path
from tkinter import Tk, Entry, Text
from tkinter.scrolledtext import ScrolledText

from .water_rights import water_rights
from .display_text_tk import display_text_tk
from .constants import *

logger = logging.getLogger(__name__)

def submit_button_tk(
        root: Tk,
        text_panel: ScrolledText,
        image_panel: Text,
        entry_filepath: Entry,
        entry_roi: Entry,
        entry_start: Entry,
        entry_end: Entry,
        output_path: Entry):
    """
    Function to handle the submit button action in a Tkinter GUI.

    Args:
        root (Tk): The root Tkinter object.
        text_panel (ScrolledText): The text panel widget.
        image_panel (Text): The image panel widget.
        entry_filepath (Entry): The entry widget for the file path.
        entry_roi (Entry): The entry widget for the ROI path.
        entry_start (Entry): The entry widget for the start year.
        entry_end (Entry): The entry widget for the end year.
        output_path (Entry): The entry widget for the output path.
    """
    year_list = []
    source_path = entry_filepath.get()
    roi_path = entry_roi.get()

    try:
        start = int(entry_start.get())
        year_list.append(start)
    except ValueError:
        logger.info("Input a valid year")
        display_text_tk(
            text="Input a valid year",
            text_panel=text_panel,
            root=root
        )

    try:
        end = int(entry_end.get())
        year_list.append(end)
    except ValueError:
        end = entry_start.get()

    output = output_path.get()

    logger.info(year_list)

    working_directory = f"{output}"
    chdir(working_directory)

    ROI_base = splitext(basename(roi_path))[0]
    DEFAULT_ROI_DIRECTORY = Path(f"{roi_path}")
    ROI_name = Path(f"{DEFAULT_ROI_DIRECTORY}")
    ROI = ROI_name

    start_month = START_MONTH
    end_month = END_MONTH

    if isfile(ROI) == True:
        # If ROI is a file, call water_rights function with the file path
        water_rights(
            ROI=ROI,
            input_directory=source_path,
            output_directory=output,
            start_year=start,
            end_year=end,
            start_month=start_month,
            end_month=end_month,
            ROI_name=None,
            figure_directory=None,
            working_directory=None,
            subset_directory=None,
            nan_subset_directory=None,
            stack_directory=None,
            monthly_sums_directory=None,
            monthly_means_directory=None,
            monthly_nan_directory=None,
            target_CRS=None,
            remove_working_directory=None,
            root=root,
            text_panel=text_panel,
            image_panel=image_panel
        )

    elif isdir(ROI) == True:
        # If ROI is a directory, iterate over the files and call water_rights function for each .geojson file
        for items in scandir(ROI):
            if items.name.endswith(".geojson"):
                roi_name = abspath(items)

                water_rights(
                    roi_name,
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
                    monthly_sums_directory=None,
                    monthly_means_directory=None,
                    monthly_nan_directory=None,
                    target_CRS=None,
                    remove_working_directory=None,
                    root=root,
                    text_panel=text_panel,
                    image_panel=image_panel
                )
    else:
        message = "Not a valid file"

        display_text_tk(
            text=message,
            text_panel=text_panel,
            root=root
        )

        logger.info(message)
