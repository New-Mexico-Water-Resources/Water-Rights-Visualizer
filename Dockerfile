FROM condaforge/mambaforge

ENV APP_ROOT /app

# update Ubuntu package manager
RUN apt-get update
# install fish shell
RUN apt-add-repository ppa:fish-shell/release-3; apt-get -y install fish; chsh -s /usr/local/bin/fish; mamba init fish
# install dependencies
RUN mamba install -y geojson geopandas h5py rasterio seaborn termcolor tk
RUN pip install area pydrive2

# RUN add-apt-repository ppa:alessandro-strada/ppa; apt-get install google-drive-ocamlfuse

# install app
RUN mkdir ${APP_ROOT}
WORKDIR ${APP_ROOT}
ADD . ${APP_ROOT}

# RUN mamba env update -n base -f /app/water_rights.yml
RUN python setup.py install
