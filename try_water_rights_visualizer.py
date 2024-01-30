from water_rights_visualizer import water_rights_visualizer
from water_rights_visualizer.google_source import GoogleSource
from water_rights_visualizer.file_path_source import FilepathSource
import cl

boundary_filename = "~/water_rights_testing/water.right.1.geojson"
output_directory = "~/water_rights_testing/output"
temporary_directory = "~/water_rights_testing/temp"

# input_directory = "/Users/halverso/Library/CloudStorage/GoogleDrive-halverso@jpl.caltech.edu/Shared drives/NMOSE Water Rights/Landsat"
# input_datastore = FilepathSource(input_directory)
input_datastore = GoogleSource(temporary_directory=temporary_directory)

water_rights_visualizer(
    boundary_filename=boundary_filename,
    input_datastore=input_datastore,
    output_directory=output_directory
)
