from affine import Affine
from shapely.geometry import MultiPolygon, Polygon
from matplotlib.patches import Polygon

def generate_patch(polygon: Polygon, affine: Affine) -> Polygon:
    """
    Generate a patch for a given polygon using an affine transformation.

    Parameters:
    polygon (Polygon): The input polygon.
    affine (Affine): The affine transformation to be applied.

    Returns:
    Polygon: The generated patch.

    """
    # If the input polygon is a MultiPolygon, take the first polygon
    if isinstance(polygon, MultiPolygon):
        polygon = list(polygon)[0]

    # Apply the affine transformation to the coordinates of the polygon
    polygon_indices = [~affine * coords for coords in polygon.exterior.coords]

    # Create a patch using the transformed coordinates
    patch = Polygon(polygon_indices, fill=None, color="black", linewidth=1)
    
    return patch
