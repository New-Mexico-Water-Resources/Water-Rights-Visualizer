.ONESHELL:
SHELL=bash
VERSION := $(shell cat water_rights_visualizer/version.txt)

default:
	make install

version:
	$(info New Mexico Water Rights Visualizer version ${VERSION})

mamba:
ifeq ($(word 1,$(shell conda run -n base conda list mamba | grep mamba)),mamba)
	@echo "mamba already installed"
else
	-conda deactivate; conda install -y -c conda-forge "mamba>=0.23"
endif

create-blank-env:
	$(info creating blank environment)
	-conda run -n base mamba create -n water_rights

update-env-mamba:
	-conda run -n water_rights mamba env update --file water_rights.yml

environment:
	make mamba
	-conda run -n base pip install pybind11_cmake
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
	-make setuptools
	make clean
	make unit-tests f

install:
	make environment
	make clean
	make uninstall
	make install-package

remove:
	conda run -n base conda env remove -n ECOSTRESS

reinstall-hard:
	make remove
	make install

reinstall-soft:
	make uninstall
	make install-package
