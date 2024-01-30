import logging
import re
import sys
from os import makedirs
from os.path import expanduser, dirname
from typing import Union, Any

from termcolor import colored

DEFAULT_STRIP_CONSOLE = False
DEFAULT_STRIP_FILE = True

DEFAULT_FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

FILE = "blue"
DIR = "blue"
TIME = "green"
PLACE = "yellow"
VALUE = "cyan"
NAME = "yellow"

ANSI_ESCAPE = re.compile(r'\x1b[^m]*m')


def strip(text: str) -> str:
    return str(ANSI_ESCAPE.sub('', text))


def URL(text: Union[str, Any]) -> str:
    return str(colored(text, FILE))


def file(text: Union[str, Any]) -> str:
    return str(colored(text, FILE))


def dir(text: Union[str, Any]) -> str:
    return str(colored(text, DIR))


def time(text: Union[str, Any]) -> str:
    return str(colored(text, TIME))


def place(text: Union[str, Any]) -> str:
    return str(colored(text, PLACE))


def val(text: Union[str, Any]) -> str:
    return str(colored(text, VALUE))


def name(text: Union[str, Any]) -> str:
    return str(colored(text, NAME))


class Formatter(logging.Formatter):
    def __init__(
            self,
            *args,
            fmt: str = DEFAULT_FORMAT,
            datefmt: str = DEFAULT_DATE_FORMAT,
            strip: bool = DEFAULT_STRIP_CONSOLE,
            color: str = None,
            **kwargs):
        super(Formatter, self).__init__(
            *args,
            fmt=fmt,
            datefmt=datefmt,
            **kwargs
        )

        self.strip = strip
        self.color = color

    def format(self, record) -> str:
        text = super(Formatter, self).format(record)

        if self.strip or self.color is not None:
            text = strip(text)

        if self.color is not None:
            text = colored(text, self.color)

        return text


def configure(
        filename: str = None,
        format: str = DEFAULT_FORMAT,
        datefmt: str = DEFAULT_DATE_FORMAT,
        strip_console: bool = DEFAULT_STRIP_CONSOLE,
        strip_file: bool = DEFAULT_STRIP_FILE):
    if isinstance(filename, str) and filename.startswith("~"):
        filename = expanduser(filename)

    handlers = []

    class InfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.INFO

    info_handler = logging.StreamHandler(sys.stdout)
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(InfoFilter())

    info_handler.setFormatter(Formatter(
        fmt=format,
        datefmt=datefmt,
        strip=strip_console
    ))

    handlers.append(info_handler)

    if filename is not None:
        makedirs(dirname(filename), exist_ok=True)

        info_file_handler = logging.FileHandler(
            filename=filename,
            mode="a"
        )

        info_file_handler.setLevel(logging.INFO)
        info_file_handler.addFilter(InfoFilter())

        info_file_handler.setFormatter(Formatter(
            fmt=format,
            datefmt=datefmt,
            strip=strip_file
        ))

        handlers.append(info_file_handler)

    class WarningFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.WARNING

    warning_handler = logging.StreamHandler(sys.stdout)
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(WarningFilter())

    warning_handler.setFormatter(Formatter(
        fmt=format,
        datefmt=datefmt,
        strip=strip_console,
        color="yellow"
    ))

    handlers.append(warning_handler)

    if filename is not None:
        warning_file_handler = logging.FileHandler(
            filename=filename,
            mode="a"
        )

        warning_file_handler.setLevel(logging.WARNING)
        warning_file_handler.addFilter(WarningFilter())

        warning_file_handler.setFormatter(Formatter(
            fmt=format,
            datefmt=datefmt,
            strip=strip_file
        ))

        handlers.append(warning_file_handler)

    class ErrorFilter(logging.Filter):
        def filter(self, record):
            return record.levelno == logging.ERROR

    error_handler = logging.StreamHandler(sys.stdout)
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(ErrorFilter())

    error_handler.setFormatter(Formatter(
        fmt=format,
        datefmt=datefmt,
        strip=strip_console,
        color="red"
    ))

    handlers.append(error_handler)

    if filename is not None:
        error_file_handler = logging.FileHandler(
            filename=filename,
            mode="a"
        )

        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.addFilter(ErrorFilter())

        error_file_handler.setFormatter(Formatter(
            fmt=format,
            datefmt=datefmt,
            strip=strip_file
        ))

        handlers.append(error_file_handler)

    while logging.root.hasHandlers():
        logging.root.removeHandler(logging.root.handlers[0])

    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers
        # force=True
    )


configure()
