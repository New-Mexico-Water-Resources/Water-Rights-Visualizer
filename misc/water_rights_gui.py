#!/usr/bin/env python
# coding: utf-8
import sys
from logging import getLogger

from water_rights_visualizer.water_rights_gui_tk import water_rights_gui_tk

logger = getLogger(__name__)


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

    if "--start-year" in argv:
        start_year = str(argv[argv.index("--start-year") + 1])
    else:
        start_year = None

    if "--end-year" in argv:
        end_year = str(argv[argv.index("--end-year") + 1])
    else:
        end_year = None

    water_rights_gui_tk(
        boundary_filename=boundary_filename,
        output_directory=output_directory,
        input_directory=input_directory,
        start_year=start_year,
        end_year=end_year
    )


if __name__ == "__main__":
    main(argv=sys.argv)
