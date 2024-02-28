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

import raster as rt

from .errors import FileUnavailable
from .data_source import DataSource
from .google_drive import google_drive_login

logger = logging.getLogger(__name__)

REMOVE_TEMPORARY_FILES = True

class S3Source(DataSource):
    def __init__(
            self,
            bucket_name: str = None,
            temporary_directory: str = None,
            S3_table_filename: str = None,
            remove_temporary_files: bool = None):
        if remove_temporary_files is None:
            remove_temporary_files = REMOVE_TEMPORARY_FILES

        if temporary_directory is None:
            temporary_directory = "temp"

        temporary_directory = abspath(expanduser(temporary_directory))

        logger.info(f"S3 temporary directory: {temporary_directory}")

        makedirs(temporary_directory, exist_ok=True)

        if S3_table_filename is None:
            S3_table_filename = join(
                abspath(dirname(__file__)), "S3_filenames.csv")

        S3_table = pd.read_csv(S3_table_filename)

        bucket = boto3.resource("s3").Bucket(bucket_name)

        self.bucket_name = bucket_name
        self.bucket = bucket
        self.temporary_directory = temporary_directory
        self.S3_table = S3_table
        self.filenames = {}
        self.remove_temporary_files = remove_temporary_files

    def inventory(self):
        dates_available = [parser.parse(str(d)).date()
                           for d in self.S3_table.date]
        years_available = list(
            set(sorted([date_step.year for date_step in dates_available])))

        return years_available, dates_available

    @contextlib.contextmanager
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        key = f"{int(tile):06d}_{str(variable_name)}_{acquisition_date:%Y-%m-%d}"

        if key in self.filenames:
            return self.filenames[key]

        if isinstance(acquisition_date, str):
            acquisition_date = parser.parse(acquisition_date).date()

        acquisition_date = acquisition_date.strftime("%Y-%m-%d")

        filtered_table = self.S3_table[self.S3_table.apply(lambda row: row.tile == int(
            tile) and row.variable == variable_name and parser.parse(str(row.date)).date().strftime(
            "%Y-%m-%d") == acquisition_date, axis=1)]

        if len(filtered_table) == 0:
            raise FileUnavailable(
                f"no files found for tile {tile} variable {variable_name} date {acquisition_date}")

        filename_base = str(filtered_table.iloc[0].filename)
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
                f"retrieving {cl.file(filename_base)} from S3 bucket {cl.name(self.bucket_name)} to file: {cl.file(filename)}")
            start_time = time.perf_counter()
            self.bucket.download_file(filename_base, filename)
            end_time = time.perf_counter()
            duration_seconds = end_time - start_time

            if not exists(filename):
                raise IOError(f"unable to retrieve file: {filename}")

            logger.info(
                f"temporary file retrieved from S3 in {cl.time(duration_seconds)} seconds: {cl.file(filename)}")
        
        self.filenames[key] = filename

        yield filename

        if self.remove_temporary_files:
            logger.info(f"removing temporary file: {filename}")
            os.remove(filename)
