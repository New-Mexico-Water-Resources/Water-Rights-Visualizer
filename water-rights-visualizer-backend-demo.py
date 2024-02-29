from os import makedirs
import shutil
import sys
from os.path import join, exists
import logging
from time import sleep
import json

from water_rights_visualizer.write_status import write_status

logger = logging.getLogger(__name__)

def main(argv=sys.argv):
    logger.info("running demo backend")
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

    for year in range(start_year, end_year + 1):
        write_status(
            message=f"processing {name} {year}",
            status_filename=status_filename 
        )
        
        sleep(10)
        image_filename_source = join("test_images", f"{year}_test_target.png")

        if not exists(image_filename_source):
            write_status(
                message=f"no image produced for {name} for year {year}",
                status_filename=status_filename
            )

            continue

        image_directory = join(working_directory, "output", "figures")
        makedirs(image_directory, exist_ok=True)
        image_filename_destination = join(image_directory, f"{year}_{name}.png")
        shutil.copy(image_filename_source, image_filename_destination)
    
    write_status(
        message=f"completed {name} from {start_year} to {end_year}",
        status_filename=status_filename
    )

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
