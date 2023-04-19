.ONESHELL:
SHELL=bash
VERSION := $(shell cat water_rights_visualizer/version.txt)

default:
	make install

version:
	$(info New Mexico Water Rights Visualizer version ${VERSION})

mamba:
ifeq ($(word 1,$(shell mamba --version)),mamba)
	@echo "mamba already installed"
else
	-conda deactivate; conda install -y -c conda-forge "mamba>=0.23"
endif

create-blank-env:
	$(info creating blank water_rights environment)
	-conda run -n base mamba create -n water_rights

update-env-mamba:
	-mamba env update -n water_rights -f water_rights.yml
#	-conda run -n water_rights mamba env update --file water_rights.yml

environment:
	make mamba
	make create-blank-env
	make update-env-mamba

clean:
	$(info cleaning build)
	-rm -rvf build
	-rm -rvf dist
	-rm -rvf *.egg-info
	-rm -rvf CMakeFiles
	-rm CMakeCache.txt

uninstall:
	$(info uninstalling water_rights_visualizer package)
	-conda run -n water_rights pip uninstall water_rights_visualizer -y

setuptools:
	-conda run -n water_rights python setup.py install

install-package:
	$(info installing water_rights_visualizer package)
	-cp google_drive_key.txt water_rights_visualizer
	-make setuptools
	make clean
	make unit-tests f

install:
	-make environment
	make clean
	make uninstall
	make install-package

remove:
	mamba env remove -n water_rights

reinstall-hard:
	make remove
	make install

reinstall-soft:
	make uninstall
	make install-package

docker-build:
	-cp google_drive_key.txt water_rights_visualizer
	docker build -t water-rights-visualizer .
