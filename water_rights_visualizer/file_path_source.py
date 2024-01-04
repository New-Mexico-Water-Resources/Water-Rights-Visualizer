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

logger = logging.getLogger(__name__)

class FilepathSource(DataSource):
    def __init__(self, directory: str):
        directory = abspath(expanduser(directory))

        if not exists(directory):
            raise IOError(f"directory not found: {directory}")

        self.directory = directory

    def date_directory(self, acquisition_date: Union[date, str]) -> str:
        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        date_directory = join(self.directory, f"{acquisition_date:%Y.%m.%d}")

        return date_directory

    def inventory(self):
        date_directory_pattern = join(self.directory, "*")
        logger.info(
            f"searching for date directories with pattern: {cl.val(date_directory_pattern)}")
        date_directories = sorted(glob(date_directory_pattern))
        date_directories = [
            directory for directory in date_directories if isdir(directory)]
        logger.info(
            f"found {cl.val(len(date_directories))} date directories under {cl.dir(self.directory)}")
        dates_available = [datetime.strptime(
            basename(directory), "%Y.%m.%d").date() for directory in date_directories]
        years_available = list(
            set(sorted([date_step.year for date_step in dates_available])))
        logger.info(
            f"counted {cl.val(len(years_available))} year available in date directories")

        return years_available, dates_available

    @contextlib.contextmanager
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        raster_directory = self.date_directory(acquisition_date)
        pattern = join(raster_directory, "**",
                       f"*_{tile}_*_{variable_name}.tif")
        logger.info(f"searching pattern: {cl.val(pattern)}")
        matches = sorted(glob(pattern, recursive=True))

        if len(matches) == 0:
            raise FileUnavailable(
                f"no files found for tile {tile} variable {variable_name} date {acquisition_date}")

        input_filename = matches[0]
        logger.info(
            f"file for tile {cl.place(tile)} variable {cl.name(variable_name)} date {cl.time(acquisition_date)}: {cl.file(input_filename)}")

        yield input_filename
