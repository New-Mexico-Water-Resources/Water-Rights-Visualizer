class FileUnavailable(IOError):
    """
    Exception raised when a file is unavailable.
    """
    pass

class BlankOutput(ValueError):
    """
    Exception raised when the output is blank.
    """
    pass
