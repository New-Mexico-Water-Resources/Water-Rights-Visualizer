from datetime import date, datetime
from logging import getLogger
from os import makedirs
from os.path import exists, join, dirname
from typing import List

import h5py
import numpy as np
from affine import Affine
from shapely import Polygon

from .constants import WGS84
from .data_source import DataSource
from .errors import BlankOutput, FileUnavailable
from .generate_subset import generate_subset
from .interpolate_stack import interpolate_stack

logger = getLogger(__name__)

def generate_stack(
        ROI_name: str,
        ROI_latlon,
        year: int,
        ROI_acres: float,
        input_datastore: DataSource,
        subset_directory: str,
        dates_available: List[date],
        stack_filename: str,
        target_CRS: str = None) -> (np.ndarray, np.ndarray, Affine):
    """
    Generates a stack of data for a given region of interest (ROI) and year.

    Args:
        ROI_name (str): The name of the region of interest.
        ROI_latlon (Polygon): The polygon representing the latitude and longitude coordinates of the ROI.
        year (int): The year for which the stack is generated.
        ROI_acres (float): The area of the ROI in acres.
        source_directory (str): The directory containing the source data.
        subset_directory (str): The directory where the generated subset will be saved.
        dates_available (List[date]): A list of available dates for the data.
        stack_filename (str): The filename of the generated stack.
        target_CRS (str, optional): The target coordinate reference system (CRS) for the stack. Defaults to None.

    Returns:
        Tuple[np.ndarray, np.ndarray, Affine]: A tuple containing the generated stack, the interpolated stack, and the affine transformation.
    """
    if target_CRS is None:
        target_CRS = WGS84

    if exists(stack_filename):
        logger.info(f"loading existing stack: {stack_filename}")

        with h5py.File(stack_filename, "r") as stack_file:
            logger.info(f"loading ET: {stack_filename}")
            ET_stack = np.array(stack_file["ET"])
            logger.info(f"loading PET: {stack_filename}")
            PET_stack = np.array(stack_file["PET"])
            affine = Affine(*list(stack_file["affine"]))

        return ET_stack, PET_stack, affine

    logger.info(f"generating stack")

    ET_sparse_stack = None
    ESI_sparse_stack = None

    dates_in_year = [
        date_step
        for date_step
        in dates_available
        if date_step.year == year
    ]

    dates_in_year = sorted(set(dates_in_year))

    if len(dates_in_year) == 0:
        raise ValueError(f"no dates for year: {year}")

    for date_step in dates_in_year:
        logger.info(f"date: {date_step.strftime('%Y-%m-%d')}")

        if not exists(subset_directory):
            logger.info(f"creating subset directory: {subset_directory}")
            makedirs(subset_directory)

        ET_subset_filename = join(subset_directory, f"{date_step.strftime('%Y.%m.%d')}_{ROI_name}_ET_subset.tif")
        logger.info(f"ET subset file: {ET_subset_filename}")
        ESI_subset_filename = join(subset_directory, f"{date_step.strftime('%Y.%m.%d')}_{ROI_name}_ESI_subset.tif")
        logger.info(f"ESI subset file: {ESI_subset_filename}")

        try:
            ET_subset, affine = generate_subset(
                input_datastore=input_datastore,
                acquisition_date=date_step,
                ROI_name=ROI_name,
                ROI_latlon=ROI_latlon,
                ROI_acres=ROI_acres,
                variable_name="ET",
                subset_filename=ET_subset_filename,
                target_CRS=target_CRS
            )
        except BlankOutput as e:
            logger.warning(e)
            continue
        except FileUnavailable as e:
            logger.warning(e)
            continue
        except Exception as e:
            logger.exception(e)
            logger.info(f"problem generating ET subset for date: {date_step.strftime('%Y-%m-%d')}")
            continue

        try:
            ESI_subset, affine = generate_subset(
                input_datastore=input_datastore,
                acquisition_date=date_step,
                ROI_name=ROI_name,
                ROI_latlon=ROI_latlon,
                ROI_acres=ROI_acres,
                variable_name="ESI",
                subset_filename=ESI_subset_filename,
                target_CRS=target_CRS
            )
        except BlankOutput as e:
            logger.warning(e)
            continue
        except FileUnavailable as e:
            logger.warning(e)
            continue
        except Exception as e:
            logger.exception(e)
            logger.info(f"problem generating ESI subset for date: {date_step.strftime('%Y-%m-%d')}")
            continue

        subset_shape = ESI_subset.shape
        rows, cols = subset_shape
        month = date_step.month
        day = date_step.day

        if ET_sparse_stack is None:
            days_in_year = (datetime(year, 12, 31) - datetime(year, 1, 1)).days + 1
            ET_sparse_stack = np.full((days_in_year, rows, cols), np.nan, dtype=np.float32)

        if ESI_sparse_stack is None:
            days_in_year = (datetime(year, 12, 31) - datetime(year, 1, 1)).days + 1
            ESI_sparse_stack = np.full((days_in_year, rows, cols), np.nan, dtype=np.float32)

        day_of_year = (datetime(year, month, day) - datetime(year, 1, 1)).days - 1

        ET_doy_image = ET_sparse_stack[day_of_year, :, :]
        ET_sparse_stack[day_of_year, :, :] = np.where(np.isnan(ET_doy_image), ET_subset, ET_doy_image)

        ESI_doy_image = ESI_sparse_stack[day_of_year, :, :]
        ESI_sparse_stack[day_of_year, :, :] = np.where(np.isnan(ESI_doy_image), ESI_subset, ESI_doy_image)

    if ET_sparse_stack is None:
        raise ValueError("no ET stack generated")

    if ESI_sparse_stack is None:
        raise ValueError("no ESI stack generated")

    PET_sparse_stack = ET_sparse_stack / ESI_sparse_stack

    logger.info(f"interpolating ET stack for year: {year}")
    ET_stack = interpolate_stack(ET_sparse_stack)
    PET_stack = interpolate_stack(PET_sparse_stack)

    stack_directory = dirname(stack_filename)

    if not exists(stack_directory):
        makedirs(stack_directory)

    logger.info(f"writing stack: {stack_filename}")
    with h5py.File(stack_filename, "w") as stack_file:
        stack_file["ET"] = ET_stack
        stack_file["PET"] = PET_stack

        stack_file["affine"] = (
            affine.a,
            affine.b,
            affine.c,
            affine.d,
            affine.e,
            affine.f
        )

    return ET_stack, PET_stack, affine
