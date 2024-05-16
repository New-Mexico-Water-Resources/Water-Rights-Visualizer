from os import makedirs
import shutil
import sys
from os.path import join, exists, basename
import logging
from time import sleep
import json
import boto3

from water_rights_visualizer import water_rights_visualizer
from water_rights_visualizer.S3_source import S3Source
from water_rights_visualizer.file_path_source import FilepathSource
import cl

logger = logging.getLogger(__name__)

# FIXME input and output bucket names need to be parameterized
input_bucket_name = "jpl-nmw-dev-inputs"
output_bucket_name = "jpl-nmw-dev-outputs"

def write_status(status_filename: str, message: str):
    logger.info(message)

    with open(status_filename, "w") as file:
        file.write(message)

def main(argv=sys.argv):
    logger.info("running operational backend")
    config_filename = argv[1]
    logger.info(f"config file: {config_filename}")

    with open(config_filename, "r") as file:
        config = json.load(file)

    name = config["name"]
    logger.info(f"name: {name}")
    start_year = int(config["start_year"])
    logger.info(f"start year: {start_year}")
    end_year = int(config['end_year'])
    logger.info(f"end year: {end_year}")
    working_directory = config["working_directory"]
    logger.info(f"working directory: {working_directory}")
    geojson_filename = config["geojson_filename"]
    logger.info(f"GeoJSON file: {geojson_filename}")
    status_filename = config["status_filename"]
    logger.info(f"status file: {status_filename}")

    temporary_directory = join(working_directory, "temp")
    output_directory = join(working_directory, "output")

    # FIXME assign figure directory and monthly means directory to directories outside of the temporary run directory
    figure_directory = None
    monthly_means_directory = None

    input_datastore = S3Source(
        bucket_name=input_bucket_name,
        temporary_directory=temporary_directory, 
        remove_temporary_files=False
    )

    session = boto3.Session()
    s3 = session.resource("s3")
    output_bucket = s3.Bucket(output_bucket_name)

    start_year = int(start_year)
    end_year = int(end_year)
    years = range(start_year, end_year + 1)

    for year in years:
        write_status(status_filename, f"processing {name} for {year}")

        water_rights_visualizer(
            boundary_filename=geojson_filename,
            input_datastore=input_datastore,
            output_directory=output_directory,
            figure_directory=figure_directory,
            monthly_means_directory=monthly_means_directory,
            start_year=year,
            end_year=year,
        )

        figure_output_filename = join(output_directory, "figures", name, f"{year}_{name}.png")

        if not exists(figure_output_filename):
            write_status(status_filename, f"problem producing figure for {name} for {year}")
            continue

        # TODO upload output file to S3 bucket
        figure_output_filename_base = basename(figure_output_filename)
        output_bucket.upload_file(figure_output_filename, figure_output_filename_base)

        CSV_output_filename = join(output_directory, "monthly_means", name, f"{year}_monthly_means.csv")

        if not exists(CSV_output_filename):
            write_status(status_filename, f"problem producing CSV for {name} for {year}")
            continue

        CSV_output_filename_base = basename(CSV_output_filename)
        output_bucket.upload_file(CSV_output_filename, CSV_output_filename_base)

        #todo:
        #pull out csv file that corresponds to png
        #delete run directory of all tiff files for this current year
        
    write_status(status_filename, f"completed {name} from {start_year} to {end_year}")

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
