FROM condaforge/mambaforge as base

ENV APP_ROOT /app

# update Ubuntu package manager
RUN apt-get update
RUN apt update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
RUN apt install -y software-properties-common

# install fish shell
RUN apt-add-repository ppa:fish-shell/release-3; apt-get -y install fish; chsh -s /usr/local/bin/fish; mamba init fish

FROM base as javascript

# install javascript
RUN apt-get -y install nodejs npm

FROM javascript as python

# install dependencies
RUN mamba install -y -c conda-forge "python=3.10" cython gdal pygeos pygrib pyresample 
RUN pip install area astropy affine boto3 h5py geojson geopandas jupyter matplotlib numpy pandas pillow pydrive2 pygeos pyresample "rasterio>1.0.0" scikit-image scipy seaborn shapely termcolor tk

FROM python as app

# install app
RUN mkdir ${APP_ROOT}
WORKDIR ${APP_ROOT}
ADD . ${APP_ROOT}

RUN mkdir /root/data

# RUN mamba env update -n base -f /app/water_rights.yml
RUN python setup.py install
RUN npm install

#install cronjob for water_report_queue
RUN apt-get install -y cron

COPY water_report_queue_cron /etc/cron.d/water_report_queue_cron
 
# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/water_report_queue_cron

# Apply cron job
RUN crontab /etc/cron.d/water_report_queue_cron

COPY init.sh /init.sh

RUN chmod +x /init.sh

RUN touch /tmp/cron_log.txt

EXPOSE 80

ENTRYPOINT /init.sh