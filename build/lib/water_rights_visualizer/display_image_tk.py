import logging
from tkinter import Text

import PIL

logger = logging.getLogger(__name__)

def display_image_tk(filename: str, image_panel: Text = None):
    """
    Display an image in a Tkinter Text widget.

    Args:
        filename (str): The path to the image file.
        image_panel (Text, optional): The Tkinter Text widget to display the image in.

    Returns:
        None
    """

    global im_resize

    if image_panel is not None:
        logger.info(f"opening image: {filename}")
        # Open the image file
        im = PIL.Image.open(filename)
        # Resize the image to 375x225 pixels using Bicubic interpolation
        im = im.resize((375, 225), PIL.Image.BICUBIC)
        # Create a Tkinter-compatible image object
        im_resize = PIL.ImageTk.PhotoImage(im)
        # Insert the image into the Text widget at the beginning
        image_panel.image_create('1.0', image=im_resize)
