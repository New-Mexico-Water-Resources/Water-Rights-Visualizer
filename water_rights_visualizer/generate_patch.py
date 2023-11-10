from affine import Affine
from shapely.geometry import MultiPolygon, Polygon
from matplotlib.patches import Polygon

def generate_patch(polygon: Polygon, affine: Affine) -> Polygon:
    if isinstance(polygon, MultiPolygon):
        polygon = list(polygon)[0]

    polygon_indices = [~affine * coords for coords in polygon.exterior.coords]
    patch = Polygon(polygon_indices, fill=None, color="black", linewidth=1)
    
    return patch
