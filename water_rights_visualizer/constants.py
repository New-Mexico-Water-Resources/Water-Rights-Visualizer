from os.path import join, abspath, dirname

ARD_TILES_FILENAME = join(abspath(dirname(__file__)), "ARD_tiles.geojson")

START_YEAR = 1985
END_YEAR = 2020
START_MONTH = 1
END_MONTH = 12
TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01
BUFFER_METERS = 2000
BUFFER_DEGREES = 0.001
CELL_SIZE_DEGREES = 0.0003
CELL_SIZE_METERS = 30

CANVAS_HEIGHT_TK = 600
CANVAS_WIDTH_TK = 700

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
UTM = "+proj=utm +zone=13 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
