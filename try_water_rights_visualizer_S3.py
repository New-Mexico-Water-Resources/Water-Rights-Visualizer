from water_rights_visualizer import water_rights_visualizer
from water_rights_visualizer.S3_source import S3Source
from water_rights_visualizer.file_path_source import FilepathSource
import cl

boundary_filename = "~/water_rights_testing/water.right.1.geojson"
output_directory = "~/water_rights_testing/output"
temporary_directory = "~/water_rights_testing/temp"
bucket_name = "jpl-nmw-dev-inputs"
start_year = 2010
end_year = 2010

input_datastore = S3Source(
    bucket_name=bucket_name,
    temporary_directory=temporary_directory, 
    remove_temporary_files=False
)

water_rights_visualizer(
    boundary_filename=boundary_filename,
    input_datastore=input_datastore,
    output_directory=output_directory,
    start_year=start_year,
    end_year=end_year,
)
