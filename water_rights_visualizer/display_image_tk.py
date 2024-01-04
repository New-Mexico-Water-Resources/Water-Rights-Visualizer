import logging
from tkinter import Text

import PIL

logger = logging.getLogger(__name__)

def display_image_tk(filename: str, image_panel: Text = None):
    global im_resize

    if image_panel is not None:
        logger.info(f"opening image: {filename}")
        im = PIL.Image.open(filename)
        im = im.resize((375, 225), PIL.Image.BICUBIC)
        im_resize = PIL.ImageTk.PhotoImage(im)
        image_panel.image_create('1.0', image=im_resize)
