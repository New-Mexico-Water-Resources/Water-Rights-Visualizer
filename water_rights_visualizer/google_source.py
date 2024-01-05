import contextlib
import os
import time
from os import makedirs
from os.path import join, abspath, dirname, exists

import pandas as pd
from dateutil import parser
from pydrive2.drive import GoogleDrive
import logging
import cl

from .errors import FileUnavailable
from .data_source import DataSource
from .google_drive import google_drive_login

logger = logging.getLogger(__name__)

class GoogleSource(DataSource):
    """
    A class representing a data source from Google Drive.

    Args:
        drive (GoogleDrive, optional): The GoogleDrive object to use for authentication. Defaults to None.
        temporary_directory (str, optional): The directory to store temporary files. Defaults to None.
        ID_table_filename (str, optional): The filename of the ID table. Defaults to None.
        key_filename (str, optional): The filename of the key file. Defaults to None.
        client_secrets_filename (str, optional): The filename of the client secrets file. Defaults to None.
    """

    def __init__(
            self,
            drive: GoogleDrive = None,
            temporary_directory: str = None,
            ID_table_filename: str = None,
            key_filename: str = None,
            client_secrets_filename: str = None):
        """
        Initializes a GoogleSource object.

        Args:
            drive (GoogleDrive, optional): The GoogleDrive object to use for authentication. Defaults to None.
            temporary_directory (str, optional): The directory to store temporary files. Defaults to None.
            ID_table_filename (str, optional): The filename of the ID table. Defaults to None.
            key_filename (str, optional): The filename of the key file. Defaults to None.
            client_secrets_filename (str, optional): The filename of the client secrets file. Defaults to None.
        """
        if drive is None:
            drive = google_drive_login(
                key_filename=key_filename,
                client_secrets_filename=client_secrets_filename
            )

        if temporary_directory is None:
            temporary_directory = "temp"

        makedirs(temporary_directory, exist_ok=True)

        if ID_table_filename is None:
            ID_table_filename = join(
                abspath(dirname(__file__)), "google_drive_file_IDs.csv")

        ID_table = pd.read_csv(ID_table_filename)

        self.drive = drive
        self.temporary_directory = temporary_directory
        self.ID_table = ID_table
        self.filenames = {}
