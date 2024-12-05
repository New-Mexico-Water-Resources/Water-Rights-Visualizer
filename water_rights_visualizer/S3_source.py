import contextlib
import os
import time
from os import makedirs
from os import remove
from os.path import join, abspath, dirname, exists, expanduser

import boto3

import pandas as pd
from dateutil import parser
import logging
import cl

import rasterio
import raster
import raster as rt

from .errors import FileUnavailable
from .data_source import DataSource
from .variable_types import get_available_variable_source_for_date, get_available_variables_for_date

# from .google_drive import google_drive_login

logger = logging.getLogger(__name__)

REMOVE_TEMPORARY_FILES = True


def read_geometry(S3_URL: str, session: boto3.session.Session = None) -> raster.RasterGeometry:
    if session is None:
        session = assume_role()

    with rasterio.Env(rasterio.session.AWSSession(session)) as env:
        with rasterio.open(S3_URL) as remote_file:
            source_CRS = remote_file.crs
            source_rows, source_cols = remote_file.shape
            source_affine = remote_file.transform

            source_grid = raster.RasterGrid.from_affine(
                affine=source_affine, rows=source_rows, cols=source_cols, crs=source_CRS
            )

            return source_grid


def read_subset(S3_URL: str, geometry: raster.RasterGeometry, session: boto3.session.Session = None) -> raster.Raster:
    if session is None:
        session = assume_role()

    with rasterio.Env(rasterio.session.AWSSession(session)) as env:
        subset = raster.Raster.open(filename=S3_URL, geometry=geometry)

    return subset


class S3Source(DataSource):
    def __init__(
        self,
        bucket_name: str = None,
        region_name: str = None,
        temporary_directory: str = None,
        S3_table_filename: str = None,
        remove_temporary_files: bool = None,
    ):
        if remove_temporary_files is None:
            remove_temporary_files = REMOVE_TEMPORARY_FILES

        if temporary_directory is None:
            temporary_directory = "temp"

        temporary_directory = abspath(expanduser(temporary_directory))

        logger.info(f"S3 temporary directory: {temporary_directory}")

        makedirs(temporary_directory, exist_ok=True)

        if S3_table_filename is None:
            S3_table_filename = join(abspath(dirname(__file__)), "S3_filenames.csv")

        S3_table = pd.read_csv(S3_table_filename)

        bucket = boto3.resource("s3", region_name=region_name).Bucket(bucket_name)

        self.bucket_name = bucket_name
        self.bucket = bucket
        self.region_name = region_name
        self.temporary_directory = temporary_directory
        self.S3_table = S3_table
        self.filenames = {}
        self.remove_temporary_files = remove_temporary_files

    def inventory(self):
        dates_available = []
        for date in self.S3_table.date:
            try:
                available_date = parser.parse(str(date)).date()
                # Check variables to see if we care about this date
                variables = get_available_variables_for_date(available_date)
                if len(variables) > 0:
                    if available_date.day == 1:
                        dates_available.append(available_date)
                    else:
                        # If it's not the first of the month, make sure we have a non-monthly data source
                        for variable in variables:
                            if not variable.monthly:
                                dates_available.append(available_date)
                                break
            except Exception as e:
                logger.warning(e)
                logger.warning(f"unable to parse date: {date}")
        years_available = list(set(sorted([date_step.year for date_step in dates_available])))

        return years_available, dates_available

    @contextlib.contextmanager
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        variable_source = get_available_variable_source_for_date(variable_name, acquisition_date)
        if not variable_source:
            logger.warn(f"no variable source found for {variable_name} on {acquisition_date}")
            return ""
        mapped_variable = variable_source.mapped_variable

        date_str = f"{acquisition_date:%Y-%m}-01" if variable_source.monthly else f"{acquisition_date:%Y-%m-%d}"

        key = f"{int(tile):06d}_{str(mapped_variable)}_{date_str}"

        if key in self.filenames:
            return self.filenames[key]

        # acquisition_date = acquisition_date.strftime("%Y-%m-%d")

        filtered_table = self.S3_table[
            self.S3_table.apply(
                lambda row: row.tile == int(tile)
                and row.variable == mapped_variable
                and parser.parse(str(row.date)).date().strftime("%Y-%m-%d") == date_str,
                axis=1,
            )
        ]

        if len(filtered_table) == 0:
            raise FileUnavailable(f"no files found for tile {tile} variable {variable_name} date {date_str}")

        matching_file_metadata = filtered_table.iloc[0]

        filename_base = str(matching_file_metadata.filename)
        filename = join(self.temporary_directory, filename_base)

        if exists(filename):
            try:
                image = rt.Raster.open(filename)
            except Exception as e:
                logger.warning(e)
                logger.warning(f"removing corrupted file: {filename}")
                remove(filename)

        if not exists(filename):
            logger.info(
                f"retrieving {cl.file(filename_base)} from S3 bucket {cl.name(self.bucket_name)} to file: {cl.file(filename)}"
            )

            failed_to_retrieve = False
            start_time = time.perf_counter()
            try:
                self.bucket.download_file(filename_base, filename)
            except Exception as e:
                logger.error(f"Failed to retrieve file from S3: {filename_base} ({filename}) - {e}")
                failed_to_retrieve = True
            end_time = time.perf_counter()
            duration_seconds = end_time - start_time

            if not failed_to_retrieve:
                logger.info(f"temporary file retrieved from S3 in {cl.time(duration_seconds)} seconds: {cl.file(filename)}")

        self.filenames[key] = filename

        yield filename

        if self.remove_temporary_files:
            logger.info(f"removing temporary file: {filename}")
            os.remove(filename)
