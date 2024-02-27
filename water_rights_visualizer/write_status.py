from os import makedirs
from os.path import dirname
import logging

from tkinter import Tk
from tkinter.scrolledtext import ScrolledText

from .display_text_tk import display_text_tk

logger = logging.getLogger(__name__)

def write_status(
        message: str, 
        status_filename: str = None,
        text_panel: ScrolledText = None, 
        root: Tk = None):
    logger.info(message)

    if status_filename is not None:
        makedirs(dirname(status_filename), exist_ok=True)
        with open(status_filename, "w") as file:
            file.write(message)

    display_text_tk(
        text=message,
        text_panel=text_panel,
        root=root
    )
