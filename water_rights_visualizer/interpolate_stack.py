import numpy as np
from scipy.interpolate import interp1d

def interpolate_stack(stack: np.ndarray) -> np.ndarray:
    """
    This function interpolates a 3D numpy array along the time axis (0th axis).
    It uses nearest interpolation to fill in missing values in the time series data for each pixel.

    Parameters:
    stack (np.ndarray): A 3D numpy array representing a stack of 2D images over time.

    Returns:
    np.ndarray: The interpolated stack.
    """
    # Get the shape of the stack
    days, rows, cols = stack.shape

    # Initialize an array to hold the interpolated stack
    filled_stack = np.full((days, rows, cols), np.nan, dtype=np.float32)

    # Loop over each pixel in the image
    for row in range(rows):
        for col in range(cols):
            # Get the time series for the current pixel
            pixel_timeseries = stack[:, row, col]

            # Create an array representing the time axis
            x = np.arange(days)

            # Find the indices of known (non-NaN) values
            known_indices = ~np.isnan(pixel_timeseries)
            known_days = x[known_indices]

            # If there are less than 3 known values, skip this pixel
            if len(known_days) < 3:
                continue

            # Get the known values from the time series
            pixel_timeseries = pixel_timeseries[known_indices]

            # Create an interpolation function for the known values
            f = interp1d(known_days, pixel_timeseries, axis=0, kind="nearest", fill_value="extrapolate")

            # Use the interpolation function to fill in the missing values
            y = f(x)

            # Store the interpolated time series in the filled stack
            filled_stack[:, row, col] = y
    
    # Return the filled stack
    return filled_stack
