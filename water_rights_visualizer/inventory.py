from datetime import datetime
from glob import glob
from os import listdir
from os.path import basename, isdir, join
from typing import List

def inventory(source_directory: str) -> (List[int], List[str]):
    date_directories = sorted(glob(join(source_directory, "*")))
    date_directories = [directory for directory in date_directories if isdir(directory)]
    dates_available = [datetime.strptime(basename(directory), "%Y.%m.%d").date() for directory in date_directories]
    years_available = list(set(sorted([date_step.year for date_step in dates_available])))
    
    return years_available, dates_available
