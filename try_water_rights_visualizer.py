from water_rights_visualizer import water_rights_visualizer, FilepathSource, GoogleSource
import cl

boundary_filename = "/Users/halverso/Desktop/water_rights_testing/water.right.1.geojson"
output_directory = "/Users/halverso/Desktop/water_rights_testing/output"

# input_directory = "/Users/halverso/Library/CloudStorage/GoogleDrive-halverso@jpl.caltech.edu/Shared drives/NMOSE Water Rights/Landsat"
# input_datastore = FilepathSource(input_directory)
input_datastore = GoogleSource()

water_rights_visualizer(
    boundary_filename=boundary_filename,
    input_datastore=input_datastore,
    output_directory=output_directory
)
