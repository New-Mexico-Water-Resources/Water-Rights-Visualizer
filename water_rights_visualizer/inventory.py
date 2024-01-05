from datetime import datetime
from glob import glob
from os import listdir
from os.path import basename, isdir, join
from typing import List

def inventory(source_directory: str) -> (List[int], List[str]):
    """
    Retrieve the years and dates available in the source directory.

    Args:
        source_directory (str): The path to the source directory.

    Returns:
        Tuple[List[int], List[str]]: A tuple containing the list of available years and dates.
    """
    # Get a list of all directories in the source directory
    date_directories = sorted(glob(join(source_directory, "*")))

    # Filter out non-directory entries
    date_directories = [directory for directory in date_directories if isdir(directory)]

    # Extract the dates from the directory names
    dates_available = [datetime.strptime(basename(directory), "%Y.%m.%d").date() for directory in date_directories]

    # Get the unique years from the available dates
    years_available = list(set(sorted([date_step.year for date_step in dates_available])))

    return years_available, dates_available
