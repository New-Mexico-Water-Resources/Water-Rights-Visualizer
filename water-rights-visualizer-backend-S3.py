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

    input_datastore = S3Source(
        bucket_name=input_bucket_name,
        temporary_directory=temporary_directory, 
        remove_temporary_files=False
    )

    session = boto3.Session()
    s3 = session.resource("s3")
    output_bucket = s3.Bucket(output_bucket_name)

    # FIXME need to consolidate status update between web UI status file, desktop UI Tk text box, and console logger

    # water_rights_visualizer(
    #     boundary_filename=geojson_filename,
    #     input_datastore=input_datastore,
    #     output_directory=output_directory,
    #     start_year=start_year,
    #     end_year=end_year,
    # )

    start_year = int(start_year)
    end_year = int(end_year)
    years = range(start_year, end_year + 1)

    for year in years:
        write_status(status_filename, f"processing {name} for {year}")

        water_rights_visualizer(
            boundary_filename=geojson_filename,
            input_datastore=input_datastore,
            output_directory=output_directory,
            start_year=year,
            end_year=year,
        )

        output_filename = join(output_directory, "figures", f"{year}_{name}.png")

        if not exists(output_filename):
            write_status(status_filename, f"problem producing {name} for {year}")
            continue

        # TODO upload output file to S3 bucket
        output_filename_base = basename(output_filename)
        output_bucket.upload_file(output_filename, output_filename_base)

    write_status(status_filename, f"completed {name} from {start_year} to {end_year}")

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
