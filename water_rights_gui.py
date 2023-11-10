#!/usr/bin/env python
# coding: utf-8
from typing import List
import io
import csv
import geojson
import geopandas as gpd
import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PIL.Image
import PIL.ImageTk
import rasterio
import random
import seaborn as sns
import sys
import tkinter.font as font
from affine import Affine
from area import area
from datetime import datetime
from glob import glob
from logging import getLogger
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon
from os import chdir, getcwd, listdir, makedirs, remove, scandir
from os.path import abspath, basename, dirname, exists, isdir, isfile, join, split, splitext
from pathlib import Path
from rasterio.features import geometry_mask
from rasterio.mask import mask, raster_geometry_mask
from rasterio.warp import reproject
from rasterio.windows import Window, transform as window_transform
from scipy.interpolate import interp1d
from shapely.geometry import MultiPolygon, Point, Polygon
from shutil import rmtree
from tkinter import *
from tkinter import filedialog, scrolledtext, ttk

from water_rights_visualizer.ROI_area import ROI_area
from water_rights_visualizer.select_tiles import select_tiles
from water_rights_visualizer.inventory import inventory
from water_rights_visualizer.generate_patch import generate_patch
from water_rights_visualizer.generate_subset import generate_subset
from water_rights_visualizer.generate_stack import generate_stack
from water_rights_visualizer.process_monthly import process_monthly
from water_rights_visualizer.calculate_percent_nan import calculate_percent_nan
from water_rights_visualizer.generate_figure import generate_figure

logger = getLogger(__name__)

WGS84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
UTM = "+proj=utm +zone=13 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
BUFFER_METERS = 2000
CELL_SIZE_DEGREES = 0.0003
CELL_SIZE_METERS = 30
TILE_SELECTION_BUFFER_RADIUS_DEGREES = 0.01

def submit():
    
    year_list = []
    source_path = entry_filepath.get()
    roi_path = entry_roi.get()
    
    try:
        start = int(entry_start.get())
        year_list.append(start)
    except ValueError:
        logger.info("Input a valid year")
        texts("Input a valid year")
        
    try:
        end = int(entry_end.get())
        year_list.append(end)
    except ValueError:
        end = entry_start.get()
    
    output = output_path.get()
    
    logger.info(year_list)
    
    working_directory = f"{output}"
    chdir(working_directory)
    
    ROI_base = splitext(basename(roi_path))[0]
    DEFAULT_ROI_DIRECTORY = Path(f"{roi_path}")
    ROI_name = Path(f"{DEFAULT_ROI_DIRECTORY}")
    ROI = ROI_name   

    def water_rights(
            ROI,
            start,
            end,
            #acres,
            output,
            source_path,
            ROI_name=None,
            source_directory=None,
            figure_directory=None,
            working_directory=None,
            subset_directory=None,
            nan_subset_directory=None,
            stack_directory=None,
            reference_directory=None,
            monthly_sums_directory=None,
            monthly_means_directory=None,
            monthly_nan_directory=None,
            target_CRS=None,
            remove_working_directory=None):
        
        ROI_base = splitext(basename(ROI))[0]
        DEFAULT_FIGURE_DIRECTORY = Path(f"{output}/figures")
        DEFAULT_SOURCE_DIRECTORY = Path(f"{source_path}")
        DEFAULT_SUBSET_DIRECTORY = Path(f"{output}/subset/{ROI_base}")
        DEFAULT_NAN_SUBSET_DIRECTORY = Path(f"{output}/nan_subsets/{ROI_base}")
        DEFAULT_MONTHLY_DIRECTORY = Path(f"{output}/monthly/{ROI_base}")
        DEFAULT_STACK_DIRECTORY = Path(f"{output}/stack/{ROI_base}")
        DEFAULT_MONTHLY_NAN_DIRECTORY = Path(f"{output}/monthly_nan/{ROI_base}")
        DEFAULT_MONTHLY_MEANS_DIRECTORY = Path(f"{output}/monthly_means/{ROI_base}")
        
        if ROI_name is None:
            ROI_name = splitext(basename(ROI))[0]

        if working_directory is None:
            working_directory = ROI_name

        if remove_working_directory is None:
            remove_working_directory = True

        if subset_directory is None:
            subset_directory = join(working_directory, DEFAULT_SUBSET_DIRECTORY)

        if nan_subset_directory is None:
            nan_subset_directory = join(working_directory, DEFAULT_NAN_SUBSET_DIRECTORY)

        if monthly_sums_directory is None:
            monthly_sums_directory = join(working_directory, DEFAULT_MONTHLY_DIRECTORY)

        if stack_directory is None:
            stack_directory = join(working_directory, DEFAULT_STACK_DIRECTORY)

        if monthly_means_directory is None:
            monthly_means_directory = join(working_directory, DEFAULT_MONTHLY_MEANS_DIRECTORY)

        if monthly_nan_directory is None:
            monthly_nan_directory = join(working_directory, DEFAULT_MONTHLY_NAN_DIRECTORY)

        if source_directory is None:
            source_directory = DEFAULT_SOURCE_DIRECTORY

        if figure_directory is None:
            figure_directory = DEFAULT_FIGURE_DIRECTORY

        if target_CRS is None:
            target_CRS = WGS84
        
        if start == end :
            str_time = datetime.now().strftime("%H%M")
            texts(f"Start Time:{str_time}\n")
            display_text01 = io.StringIO(f"Generating ET for {ROI_name}:\n{start}\n")
            output01 = display_text01.getvalue()
            text.insert(1.0, output01)
            root.update()
        else:
            str_time = datetime.now().strftime("%H%M")
            texts(f"Start Time:{str_time}\n")
            display_text01 = io.StringIO(f"Generating ET for {ROI_name}:\n{start} - {end}\n")
            output01 = display_text01.getvalue()
            text.insert(1.0, output01)
            root.update()
        
        logger.info(f"ROI name: {ROI_name}")
        logger.info(f"loading ROI: {ROI}")
        ROI_latlon = gpd.read_file(ROI).to_crs(WGS84).geometry[0]
        ROI_for_nan = list((gpd.read_file(ROI).to_crs(WGS84)).geometry)
        ROI_acres = round(ROI_area(ROI, working_directory), 2)

        years_available, dates_available = inventory(source_directory)
        monthly_means = []

        if start == end:
            years_x = [start]
        else:
            years_x = [*range(int(start), int(end)+1)]
        
        for i, year in enumerate(years_x):
            logger.info(f"processing: {year}")
            texts(f"Processing: {year}\n")
        
            
            stack_filename = join(stack_directory, f"{year:04d}_{ROI_name}_stack.h5")

            try:
                texts(f"loading stack: {stack_filename}\n")
                ET_stack, PET_stack, affine = generate_stack(
                    ROI_name=ROI_name,
                    ROI_latlon=ROI_latlon,
                    year=year,
                    ROI_acres=ROI_acres,
                    source_directory=source_directory,
                    subset_directory=subset_directory,
                    dates_available=dates_available,
                    stack_filename=stack_filename,
                    target_CRS=target_CRS
            )
            except Exception as e:
                logger.exception(e)
                logger.info(f"unable to generate stack for year: {year}")
                continue
                
            monthly_means.append(process_monthly(
                ET_stack=ET_stack,
                PET_stack=PET_stack,
                ROI_latlon=ROI_latlon,
                ROI_name=ROI_name,
                subset_affine=affine,
                CRS=target_CRS,
                year=year,
                monthly_sums_directory=monthly_sums_directory,
                monthly_means_directory=monthly_means_directory
            ))
            
            texts("Calculating uncertainty\n")
            
            calculate_percent_nan(
                ROI_for_nan,
                subset_directory,
                nan_subset_directory,
                monthly_nan_directory)
            
            texts("Generating figure\n")
            
            nan_means = []
            nd = pd.read_csv(f"{monthly_nan_directory}/{year}.csv")
            nan_means.append(nd)
            logger.info(f"application nan means: \n {nan_means}")
        
            month_means = []
            mm = pd.read_csv(f"{monthly_means_directory}/{year}_monthly_means.csv")
            month_means.append(mm)
            logger.info(f"application monthly means: \n {month_means}")

            idx =  {'Months': [3,4,5,6,7,8,9,10]}
            df1 = pd.DataFrame(idx, columns = ['Months'])
            df2 = pd.DataFrame(idx, columns = ['Months'])

            main_dfa = pd.merge(left = df1, right = mm, how = 'left', left_on = "Months", right_on = "Month")
            main_df = pd.merge(left = main_dfa, right = nd, how = 'left', left_on = "Months", right_on = "month")
            main_df = main_df.replace(np.nan,100)
            logger.info(f'main_df: {main_df}')
            
            monthly_means_df = pd.concat(month_means, axis=0)
            logger.info("monthly_means_df:")
            mean = np.nanmean(monthly_means_df["ET"])
            sd = np.nanstd(monthly_means_df["ET"])
            vmin = max(mean - 2 * sd, 0)
            vmax = mean + 2 * sd

            today = date.today()
            date= str(today)

            logger.info(f"generating figure for year: {year}")

            figure_output_directory = join(figure_directory, ROI_name)

            if not exists(figure_output_directory):
                makedirs(figure_output_directory)

            figure_filename = join(figure_output_directory, f"{year}_{ROI_name}.png")

            if exists(figure_filename):
                logger.info(f"figure already exists: {figure_filename}")
                texts(f"figure exists in working directory\n")
                add_image(figure_filename)
                continue
            
            try:
                generate_figure(
                    ROI_name=ROI_name,
                    ROI_latlon=ROI_latlon,
                    ROI_acres=ROI_latlon,
                    creation_date=date,
                    year=year,
                    vmin=vmin,
                    vmax=vmax,
                    affine=affine,
                    main_df=main_df,
                    monthly_sums_directory=monthly_sums_directory,
                    figure_filename=figure_filename,
                    texts=texts,
                    add_image=add_image
                )
            except Exception as e:
                logger.exception(e)
                logger.info(f"unable to generate figure for year: {year}")
                continue
                

    
    if isfile(ROI) == True:
        water_rights(
        ROI,
        start,
        end,
        #acres,
        output,
        source_path,
        ROI_name=None,
        source_directory=None,
        figure_directory=None,
        working_directory=None,
        subset_directory=None,
        nan_subset_directory=None,
        stack_directory=None,
        monthly_sums_directory=None,
        monthly_means_directory=None,
        monthly_nan_directory=None,
        target_CRS=None,
        remove_working_directory=None)
       
    elif isdir(ROI) == True:
        for items in scandir(ROI):
            if items.name.endswith(".geojson"):
                roi_name = abspath(items)
                water_rights(
                roi_name,
                start,
                end,
                #acres,
                output,
                source_path,
                ROI_name=None,
                source_directory=None,
                figure_directory=None,
                working_directory=None,
                subset_directory=None,
                nan_subset_directory=None,
                stack_directory=None,
                monthly_sums_directory=None,
                monthly_means_directory=None,
                monthly_nan_directory=None,
                target_CRS=None,
                remove_working_directory=None)
    else:
        texts("Not a valid file")
        logger.info("Not a valid file")
    
HEIGHT = 600
WIDTH = 700

root =  Tk()
root.title("JPL-NMOSE ET visualizer")
root.geometry("700x600")
root.resizable(0,0)

canvas = Canvas(root, height = HEIGHT, width = WIDTH )
canvas.pack()

myFont = font.Font(family='Helvetica', size = 12)

imgpath = join(dirname(abspath(sys.argv[0])), "img4.png")

# imgpath = "/Users/seamony/Desktop/WR_GUI/img4.png"


if exists(imgpath) == True:
    img = PhotoImage(file = imgpath)
    background_label = Label(root, image = img)
    background_label.place(relwidth = 1, relheight = 1)
    low_frame = Frame(root, bg = 'skyblue', bd = 4)
    low_frame.place(relx = 0.20, rely = 0.5, relwidth = 0.35, relheight = 0.4, anchor = 'n')
    img_frame = Frame(root, bg = 'skyblue', bd = 4)
    img_frame.place(relx = 0.675, rely = 0.5, relwidth = 0.60, relheight = 0.4, anchor = 'n')
else: 
    background_label = Label(root, bg = 'lightseagreen')
    background_label.place(relwidth = 1, relheight = 1)
    low_frame = Frame(root, bg = 'mediumturquoise', bd = 4)
    low_frame.place(relx = 0.20, rely = 0.5, relwidth = 0.35, relheight = 0.4, anchor = 'n')
    img_frame = Frame(root, bg = 'mediumturquoise', bd = 4)
    img_frame.place(relx = 0.675, rely = 0.5, relwidth = 0.60, relheight = 0.4, anchor = 'n')
    

text = scrolledtext.ScrolledText(low_frame, width = 200, height = 200)
text.config(state=NORMAL)
text.pack()

image = Text(img_frame, width = 200, height = 200)
image.config(state=NORMAL)
image.pack()

def texts(sometexts):
    display_text = io.StringIO(f"{sometexts}")
    output = display_text.getvalue()
    text.insert('1.0', output)
    root.update()
    
    return "break"

    
def browse_data(i):
    
    phrase = i
    
    if isdir(phrase) == True:
        landsat_file = filedialog.askdirectory(initialdir = phrase, title ="Select Landsat directory")
        if landsat_file == phrase:
            pass
        elif len(landsat_file) < 1:
            pass
        else:
            clear_data()
            entry_filepath.insert(END, landsat_file )
    else:
        landsat_file = filedialog.askdirectory(initialdir = "C:/Users/", title ="Select Landsat directory")
        if landsat_file == phrase:
            pass
        elif len(landsat_file) < 1:
            pass
        else:
            clear_data()
            entry_filepath.insert(END, landsat_file )
       
        
def browse_roi(i):

    phrase = i
    
    if isdir(phrase) == True:
        roi_file = filedialog.askopenfilename(initialdir = phrase, title ="Select geojson file")
        if roi_file == phrase:
            pass
        elif len(roi_file) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_file)
            
    elif isfile(phrase) == True:
        roi_file = filedialog.askopenfilename(initialdir = phrase, title ="Select geojson file")
        if roi_file == phrase:
            pass
        elif len(roi_file) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_file)
    
    else:
        roi_file = filedialog.askopenfilename(initialdir = "C:/Users/", title ="Select geojson file")
        if roi_file == phrase:
            pass
        elif len(roi_file) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_file)

def browse_batch(i):

    phrase = i
    
    if isdir(phrase) == True:
        roi_batch =  filedialog.askdirectory(initialdir = phrase, title ="Select outpt directory")
        if roi_batch == phrase:
            pass
        elif len(roi_batch) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_batch)
    else:
        roi_batch =  filedialog.askdirectory(initialdir = "C:/Users/", title ="Select outpt directory")
        if roi_batch == phrase:
            pass
        elif len(roi_batch) < 1:
            pass
        else:
            clear_roi()
            entry_roi.insert(END, roi_batch)
    
def browse_output(i):
    
    phrase = i
    
    if isdir(phrase) == True:
        output_file =  filedialog.askdirectory(initialdir = phrase, title ="Select outpt directory")
        if output_file == phrase:
            pass
        elif len(output_file) < 1:
            pass
        else:
            clear_output()
            output_path.insert(END, output_file)
    else:
        output_file =  filedialog.askdirectory(initialdir = "C:/Users/", title ="Select outpt directory")
        if output_file == phrase:
            pass
        elif len(output_file) < 1:
            pass
        else:
            clear_output()
            output_path.insert(END, output_file)
    

def clear_roi():    
    entry_roi.delete(0, 'end')

def clear_data():
    entry_filepath.delete(0, 'end')

def clear_output():
    output_path.delete(0, 'end')

def clear_text():
    image.delete(1.0, END)
    text.delete(1.0, END)
    progress.set(0)
    root.update()

def add_image(filepath):
    global im_resize
    logger.info(f"opening image: {filepath}")
    im = PIL.Image.open(filepath)
    im = im.resize((375, 225), PIL.Image.BICUBIC)
    im_resize = PIL.ImageTk.PhotoImage(im)
    image.image_create('1.0',image = im_resize)
    # root.image.see('1.0')
    # root.update()

def get_path(path):
    
    if path == 'Landsat':
        filepath = entry_filepath.get()
    elif path == 'Batch':
        filepath = entry_roi.get()
    elif path == 'Single':
        filepath = entry_roi.get()
    elif path == 'Output':
        filepath = output_path.get()
    else:
        logger.info(f"Error retrieving path(s)")
    
    return filepath

# GEOJSON/ROI FILEPATH
entry_roi = Entry(root, font = 10, bd = 2)
entry_roi.insert(END, "Water Rights Boundary")
#entry_roi.insert(END, "C:/Users/CashOnly/Desktop/PT-JPL/ROI_477/2035.geojson")
entry_roi['font'] = myFont
entry_roi.place(relx = 0.36, rely = 0.1, relwidth = .66, relheight = 0.05, anchor = 'n')

roi_button = Button(root, text = "Single", width = 8, command = lambda:[browse_roi(get_path('Single'))])
roi_button['font'] = myFont
roi_button.place(relx = 0.85, rely = 0.1 , relheight = 0.05)

roi_batch = Button(root, text = "Batch", width = 8, command = lambda:[browse_batch(get_path('Batch'))])
roi_batch['font'] = myFont
roi_batch.place(relx = 0.720, rely = 0.1 , relheight = 0.05)

# LANDSAT DATA FILEPATH
entry_filepath = Entry(root,  font = 10, bd = 2, borderwidth = 2)
entry_filepath.insert(END, 'Landsat Directory')
#entry_filepath.insert(END, 'E:/Personal/ISC_DATA')
entry_filepath['font'] = myFont
entry_filepath.place(relx = 0.41, rely = 0.2, relwidth = .76, relheight = 0.05, anchor = 'n')

filepath_button = Button(root, text = "Search", width  = 10, command = lambda: [ browse_data(get_path('Landsat'))])
filepath_button['font'] = myFont
filepath_button.place(relx = 0.825, rely = 0.2, relheight = 0.05)


# OUTPUT FILEPATH
output_path = Entry(root, font = 10, bd = 2)
output_path.insert(END, "Output Directory")
#output_path.insert(END, "C:/Users/CashOnly/Desktop/PT-JPL")
output_path['font'] = myFont
output_path.place(relx = 0.41, rely = 0.3, relwidth = 0.76, relheight = 0.05, anchor = 'n')

output_button = Button(root,text = "Search", width = 10, command = lambda:[browse_output(get_path('Output'))])
output_button['font'] = myFont
output_button.place(relx = 0.825, rely = 0.3, relheight = 0.05)

# START YEAR
entry_start = Entry(root, font = 10, bd = 2, justify='center')
entry_start['font'] = myFont
entry_start.place(relx = 0.09, rely = 0.4, relwidth = .12, relheight = 0.05, anchor = 'n')
#entry_start.insert(0, "2020")
entry_start.insert(0, "Start")

# END YEAR
entry_end = Entry(root, font = 10, bd = 2, justify='center')
entry_end['font'] = myFont
entry_end.place(relx = 0.24, rely = 0.4, relwidth = 0.12, relheight= 0.05, anchor = 'n')
#entry_end.insert(0, "2020")
entry_end.insert(0, "End")

#Clear Texts
clear_text = Button(root, text = 'Clear Board', width =10, command = clear_text)
clear_text['font'] = myFont
clear_text.place(relx = 0.825, rely=0.4, relheight=0.05)

# SUBMIT BUTTON
submit_button = Button(root, text = "Submit", width = 10, command = submit)
submit_button['font'] = myFont
submit_button.place(relx = 0.670, rely = 0.4, relheight = 0.05)

def main():
    root.mainloop()

if __name__ == "__main__":
    main()

