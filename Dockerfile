FROM condaforge/mambaforge

ENV APP_ROOT /app

# update Ubuntu package manager
RUN apt-get update
# install fish shell
RUN apt-add-repository ppa:fish-shell/release-3; apt-get -y install fish; chsh -s /usr/local/bin/fish; mamba init fish
# install dependencies
RUN mamba install -y geojson
RUN mamba install -y geopandas
RUN mamba install -y h5py
RUN mamba install -y rasterio
RUN mamba install -y seaborn
RUN mamba install -y termcolor
RUN mamba install -y tk
RUN pip install area

RUN add-apt-repository ppa:alessandro-strada/ppa; apt-get install google-drive-ocamlfuse


# install app
RUN mkdir ${APP_ROOT}
WORKDIR ${APP_ROOT}
ADD . ${APP_ROOT}

# RUN mamba env update -n base -f /app/water_rights.yml
RUN python setup.py install
