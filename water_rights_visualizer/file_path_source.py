import contextlib
from datetime import date, datetime
from glob import glob
from os.path import abspath, expanduser, exists, join, isdir, basename
from typing import Union

from dateutil import parser
import logging
import cl
from .errors import FileUnavailable
from .data_source import DataSource
from .variable_types import get_sources_for_variable, get_available_variable_source_for_date

logger = logging.getLogger(__name__)


class FilepathSource(DataSource):
    def __init__(self, directory: str, monthly: bool = False):
        """
        Initialize the FilepathSource object.

        Args:
            directory (str): The directory path where the files are located.

        Raises:
            IOError: If the directory does not exist.
        """
        directory = abspath(expanduser(directory))

        if not exists(directory):
            raise IOError(f"directory not found: {directory}")

        self.directory = directory
        self.monthly = monthly

    def date_directory(self, acquisition_date: Union[date, str]) -> str:
        """
        Get the directory path for a specific acquisition date.

        Args:
            acquisition_date (Union[date, str]): The acquisition date in date or string format.

        Returns:
            str: The directory path for the acquisition date.
        """
        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        date_directory = join(self.directory, f"{acquisition_date:%Y.%m.%d}")

        return date_directory

    def inventory(self):
        """
        Get the available years and dates in the directory (using ET files).

        Returns:
            tuple: A tuple containing the list of available years and dates.
        """
        years_available = []
        dates_available = []

        for variable_type in get_sources_for_variable("ET"):
            if variable_type.monthly:
                # Monthly data is in a single directory
                path = join(self.directory, variable_type.parent_dir, f"*_{variable_type.mapped_variable}.tif")
                et_files = sorted(glob(path))

                for file in et_files:
                    filename = basename(file)
                    parts = filename.split("_")
                    start_date = datetime.strptime(parts[-3], "%Y%m%d").date()
                    if start_date not in dates_available:
                        dates_available.append(start_date)
                    if start_date.year not in years_available:
                        years_available.append(start_date.year)
            else:
                # date_directory_pattern = join(self.directory, "*")
                # YYYY.MM.DD
                date_directory_pattern = join(self.directory, "[0-9]{4,4}.[0-9]{2,2}.[0-9]{2,2}")
                logger.info(f"searching for date directories with pattern: {cl.val(date_directory_pattern)}")
                date_directories = sorted(glob(date_directory_pattern))
                date_directories = [directory for directory in date_directories if isdir(directory)]
                logger.info(f"found {cl.val(len(date_directories))} date directories under {cl.dir(self.directory)}")
                for directory in date_directories:
                    date = datetime.strptime(basename(directory), "%Y.%m.%d").date()
                    if date not in dates_available:
                        dates_available.append(date)
                    if date.year not in years_available:
                        years_available.append(date.year)

                logger.info(f"counted {cl.val(len(years_available))} year available in date directories")

        return years_available, dates_available

    @contextlib.contextmanager
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        """
        Get the filename for a specific tile, variable, and acquisition date.

        Args:
            tile (str): The tile name.
            variable_name (str): The variable name.
            acquisition_date (str): The acquisition date in string format.

        Yields:
            str: The filename for the tile, variable, and acquisition date.

        Raises:
            FileUnavailable: If no files are found for the given parameters.
        """

        variable_source = get_available_variable_source_for_date(variable_name, acquisition_date)
        mapped_variable = variable_source.mapped_variable

        if variable_source.monthly:
            # if variable_name == "PET":
            #     pattern = join(self.directory, f"*_ETO_{tile}_{acquisition_date:%Y%m%d}_*_{variable_name}.tif")
            # else:
            #     pattern = join(self.directory, f"*_{tile}_{acquisition_date:%Y%m%d}_*_{variable_name}.tif")
            # # pattern = join(self.directory, f"*_{tile}_{acquisition_date:%Y%m%d}_*_{variable_name}.tif")
            # logger.info(f"searching monthly pattern: {cl.val(pattern)}")
            # matches = sorted(glob(pattern))
            pattern = join(
                self.directory,
                variable_source.parent_dir,
                f"*_{tile}_{acquisition_date:%Y%m}01_*_{mapped_variable}.tif",
            )
            logger.info(f"searching monthly pattern: {cl.val(pattern)}")
            matches = sorted(glob(pattern))
        else:
            raster_directory = self.date_directory(acquisition_date)
            pattern = join(raster_directory, "**", f"*_{tile}_*_{mapped_variable}.tif")
            logger.info(f"searching daily pattern: {cl.val(pattern)}")
            matches = sorted(glob(pattern, recursive=True))

        if len(matches) == 0:
            raise FileUnavailable(
                f"no {'month' if self.monthly else 'day'} files found for tile {tile} variable {mapped_variable} date {acquisition_date}"
            )

        input_filename = matches[0]
        logger.info(
            f"file for tile {cl.place(tile)} variable {cl.name(mapped_variable)} date {cl.time(acquisition_date)}: {cl.file(input_filename)}"
        )

        yield input_filename
