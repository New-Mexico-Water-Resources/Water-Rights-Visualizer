from abc import abstractmethod


class DataSource:
    """
    Abstract base class for data sources.
    """

    monthly = False

    @abstractmethod
    def inventory(self):
        """
        Returns the inventory of available data.
        """

        pass

    @abstractmethod
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        """
        Returns the filename for the given tile, variable name, and acquisition date.

        Args:
            tile (str): The tile identifier.
            variable_name (str): The name of the variable.
            acquisition_date (str): The acquisition date of the data.

        Returns:
            str: The filename for the data.
        """

        pass
