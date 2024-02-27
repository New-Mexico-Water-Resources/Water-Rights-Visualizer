#!/usr/bin/env python
# coding: utf-8
import logging
import sys
from os import makedirs, scandir
from os.path import basename, isdir, splitext, abspath, exists, isfile, expanduser, join, dirname
from pathlib import Path

import matplotlib as mpl

import cl
from .water_rights import water_rights
from .constants import *
from .data_source import DataSource
from .file_path_source import FilepathSource
from .google_source import GoogleSource

logger = logging.getLogger(__name__)

mpl.use("Agg")

START_YEAR = 1985
END_YEAR = 2020
START_MONTH = 1
END_MONTH = 12

def water_rights_visualizer(
        boundary_filename: str,
        output_directory: str,
        input_datastore: DataSource = None,
        input_directory: str = None,
        google_drive_temporary_directory: str = None,
        google_drive_key_filename: str = None,
        google_drive_client_secrets_filename: str = None,
        remove_temporary_google_files: bool = None,
        start_year: int = START_YEAR,
        end_year: int = END_YEAR,
        start_month: int = START_MONTH,
        end_month: int = END_MONTH,
        status_filename: str = None,
        debug=False):
    boundary_filename = abspath(expanduser(boundary_filename))
    output_directory = abspath(expanduser(output_directory))

    if not exists(boundary_filename):
        raise IOError(f"boundary filename not found: {boundary_filename}")

    logger.info(f"boundary file: {cl.file(boundary_filename)}")

    if input_datastore is None:
        if google_drive_temporary_directory is not None:
            logger.info(f"using Google Drive data source in directory: {google_drive_client_secrets_filename}")
            input_datastore = GoogleSource(
                temporary_directory=google_drive_temporary_directory,
                key_filename=google_drive_key_filename,
                client_secrets_filename=google_drive_client_secrets_filename,
                remove_temporary_files=remove_temporary_google_files
            )
        elif input_directory is not None:
            logger.info(f"using local file path data source in directory: {input_directory}")
            input_datastore = FilepathSource(directory=input_directory)
        else:
            raise ValueError("no input data source given")

    makedirs(output_directory, exist_ok=True)
    logger.info(f"output directory: {cl.dir(output_directory)}")

    working_directory = output_directory
    logger.info(f"working directory: {cl.dir(working_directory)}")

    ROI_base = splitext(basename(boundary_filename))[0]
    DEFAULT_ROI_DIRECTORY = Path(f"{boundary_filename}")
    ROI_name = Path(f"{DEFAULT_ROI_DIRECTORY}")

    logger.info(f"target: {cl.place(ROI_name)}")

    ROI = ROI_name
    BUFFER_METERS = 2000
    # BUFFER_DEGREES = 0.001
    CELL_SIZE_DEGREES = 0.0003
    CELL_SIZE_METERS = 30
    TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01
    ARD_TILES_FILENAME = join(abspath(dirname(__file__)), "ARD_tiles.geojson")

    if isfile(ROI):
        water_rights(
            ROI,
            input_datastore=input_datastore,
            output_directory=output_directory,
            start_year=start_year,
            end_year=end_year,
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
            status_filename=status_filename,
            debug=debug
        )

    elif isdir(ROI):
        for items in scandir(ROI):
            if items.name.endswith(".geojson"):
                roi_name = abspath(items)
                water_rights(
                    roi_name,
                    input_datastore=input_datastore,
                    output_directory=output_directory,
                    start_year=start_year,
                    end_year=end_year,
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
                    status_filename=status_filename,
                    debug=debug
                )
    else:
        logger.warning(f"invalid ROI: {ROI}")


def main(argv=sys.argv):
    if "--boundary-filename" in argv:
        boundary_filename = str(argv[argv.index("--boundary-filename") + 1])
    else:
        boundary_filename = None

    if "--output-directory" in argv:
        output_directory = str(argv[argv.index("--output-directory") + 1])
    else:
        output_directory = None

    if "--input-directory" in argv:
        input_directory = str(argv[argv.index("--input-directory") + 1])
    else:
        input_directory = None

    if "--google-drive-temporary-directory" in argv:
        google_drive_temporary_directory = str(argv[argv.index("--google-drive-temporary-directory") + 1])
    else:
        google_drive_temporary_directory = None

    if "--google-drive-key-filename" in argv:
        google_drive_key_filename = str(argv[argv.index("--google-drive-key-filename") + 1])
    else:
        google_drive_key_filename = None

    if "--google-drive-client-secrets-filename" in argv:
        google_drive_client_secrets_filename = str(argv[argv.index("--google-drive-client-secrets-filename") + 1])
    else:
        google_drive_client_secrets_filename = None

    if "--start-year" in argv:
        start_year = str(argv[argv.index("--start-year") + 1])
    else:
        start_year = None

    if "--end-year" in argv:
        end_year = str(argv[argv.index("--end-year") + 1])
    else:
        end_year = None

    debug = "--debug" in argv

    water_rights_visualizer(
        boundary_filename=boundary_filename,
        output_directory=output_directory,
        input_directory=input_directory,
        google_drive_temporary_directory=google_drive_temporary_directory,
        google_drive_key_filename=google_drive_key_filename,
        google_drive_client_secrets_filename=google_drive_client_secrets_filename,
        start_year=start_year,
        end_year=end_year,
        debug=debug
    )

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
