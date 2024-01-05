from abc import abstractmethod


class DataSource:
    @abstractmethod
    def inventory(self):
        pass

    @abstractmethod
    def get_filename(self, tile: str, variable_name: str, acquisition_date: str) -> str:
        pass
    