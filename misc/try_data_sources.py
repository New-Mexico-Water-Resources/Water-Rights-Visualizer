from water_rights_visualizer.google_source import GoogleSource
from water_rights_visualizer.file_path_source import FilepathSource
import cl

input_directory = "/Users/halverso/Library/CloudStorage/GoogleDrive-halverso@jpl.caltech.edu/Shared drives/NMOSE Water Rights/Landsat"

tile = "012015"
variable_name = "ESI"
acquisition_date = "2020-05-01"

file_source = FilepathSource(input_directory)

with file_source.get_filename(tile, variable_name, acquisition_date) as filename:
    print(f"file: {filename}")

drive_source = GoogleSource()

with drive_source.get_filename(tile, variable_name, acquisition_date) as filename:
    print(f"file: {filename}")
