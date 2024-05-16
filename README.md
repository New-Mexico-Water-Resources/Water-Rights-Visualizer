# Water Rights Visualizer

Gregory Halverson, Jet Propulsion Laboratory, [gregory.h.halverson@jpl.nasa.gov](mailto:gregory.h.halverson@jpl.nasa.gov)

Mony Sea, California State University Northridge

Holland Hatch, Chapman University

Annalise Jensen, Chapman University

Zoe von Allmen, Chapman University

This repository contains the code for the ET Toolbox 7-day hindcast and 7-day forecast data production system.

## Copyright

Copyright 2022, by the California Institute of Technology. ALL RIGHTS RESERVED. United States Government Sponsorship acknowledged. Any commercial use must be negotiated with the Office of Technology Transfer at the California Institute of Technology.
 
This software may be subject to U.S. export control laws. By accepting this software, the user agrees to comply with all applicable U.S. export laws and regulations. User has the responsibility to obtain export licenses, or other export authority as may be required before exporting such information to foreign countries or providing access to foreign persons.

## Requirements

This system was designed to work in a Linux-like environment and macOS using a conda environment.

### `conda`

The Water Rights Visualizer is designed to run in a Python 3 [`conda`](https://docs.conda.io/en/latest/miniconda.html) environment using [Miniconda](https://docs.conda.io/en/latest/miniconda.html) To use this environment, download and install [Miniconda](https://docs.conda.io/en/latest/miniconda.html). Make sure that your shell has been initialized for `conda`.

You should see the base environment name `(base)` when running a shell with conda active.

## Amazon Linux 2023 on AWS EC2

These are the instructions for setting up an Amazon Linux 2023 EC2 instance from scratch.

Install `make`:
```
sudo yum update
sudo yum install -y make
```

Run the `setup-amazon-linux` make target to install the `git`, `mamba`, and `docker` tools:

```
make setup-amazon-linux
```

Exit your shell and log back in. There should now be `(base)` in the prompt.

Add an SSH key to GitHub
https://docs.github.com/en/authentication/connecting-to-github-with-ssh/checking-for-existing-ssh-keys

Clone the `Water-Rights-Visualizer` repository:
```
git clone git@github.com:New-Mexico-Water-Resources/Water-Rights-Visualizer.git
```

Enter the repository directory:
```
cd Water-Rights-Visualizer
```

## Credentials

Insert `google_drive_key.txt` and `client_secrets.json` into `Water-Rights-Visualizer/water_rights_visualizer`.

## Installation

Use `make install` to produce the `water_rights` environment:

```bash
(base) $ make install
```

This should produce a conda environment called `water_rights` in your [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installation.

## Activation

To use the pipeline, you must activate the `water_rights` environment:

```bash
(base) $ conda activate water_rights
```

You should see the environment name `(water_rights)` in parentheses prepended to the command line prompt.

## Launch

To launch the Water Rights Visualizer GUI, run the `water_rights_gui.py` script:

```bash
(water_rights) $ python water_rights_gui_tk.py
```

## Deactivation

When you are done using the pipeline, you can deactivate the `water_rights` environment:

```bash
(water_rights) $ conda deactivate water_rights
```

You should see the environment name on the command line prompt change to `(base)`.

## Updating

To update your installation of the `water_rights` environment, rebuild with this command:

```bash
(base) $ make reinstall-hard
```

## Uninstallation

```bash
(base) $ make remove
```


