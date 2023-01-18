from water_rights_visualizer import water_rights_visualizer

boundary_filename = "/Users/halverso/Desktop/water_rights_testing/water.right.1.geojson"
input_directory = "/Volumes/GoogleDrive/Shared drives/NMOSE Water Rights/Landsat"
output_directory = "/Users/halverso/Desktop/water_rights_testing/output"

water_rights_visualizer(
    boundary_filename=boundary_filename,
    input_directory=input_directory,
    output_directory=output_directory
)
