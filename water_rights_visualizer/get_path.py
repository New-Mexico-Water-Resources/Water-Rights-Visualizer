import logging

logger = logging.getLogger(__name__)

def get_path(path: str, entry_filepath, entry_roi, output_path) -> str:

    if path == 'Landsat':
        filepath = entry_filepath.get()
    elif path == 'Batch':
        filepath = entry_roi.get()
    elif path == 'Single':
        filepath = entry_roi.get()
    elif path == 'Output':
        filepath = output_path.get()
    else:
        logger.info(f"Error retrieving path(s)")

    return filepath