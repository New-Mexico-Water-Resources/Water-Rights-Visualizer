import io
import sys
from os import chdir, scandir
from os.path import splitext, basename, isfile, isdir, abspath, join, dirname, exists
from pathlib import Path
from tkinter import Tk, Canvas, font as font, PhotoImage, Label, Frame, scrolledtext, NORMAL, Text, filedialog, END, Entry, Button

import PIL.Image
import PIL.ImageTk

import logging

from .get_path import get_path
from .water_rights import water_rights

logger = logging.getLogger(__name__)

def water_rights_gui(
        boundary_filename: str,
        output_directory: str,
        input_directory: str,
        start_year: str,
        end_year: str):
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

        if isfile(ROI) == True:
            water_rights(texts, text, root, add_image,
                         ROI,
                         start,
                         end,
                         # acres,
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
                    water_rights(texts, text, root, add_image,
                                 roi_name,
                                 start,
                                 end,
                                 # acres,
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

    root = Tk()
    root.title("JPL-NMOSE ET visualizer")
    root.geometry("700x600")
    root.resizable(0, 0)

    canvas = Canvas(root, height=HEIGHT, width=WIDTH)
    canvas.pack()

    myFont = font.Font(family='Helvetica', size=12)

    imgpath = join(dirname(abspath(sys.argv[0])), "img4.png")

    # imgpath = "/Users/seamony/Desktop/WR_GUI/img4.png"

    if exists(imgpath) == True:
        img = PhotoImage(file=imgpath)
        background_label = Label(root, image=img)
        background_label.place(relwidth=1, relheight=1)
        low_frame = Frame(root, bg='skyblue', bd=4)
        low_frame.place(relx=0.20, rely=0.5, relwidth=0.35, relheight=0.4, anchor='n')
        img_frame = Frame(root, bg='skyblue', bd=4)
        img_frame.place(relx=0.675, rely=0.5, relwidth=0.60, relheight=0.4, anchor='n')
    else:
        background_label = Label(root, bg='lightseagreen')
        background_label.place(relwidth=1, relheight=1)
        low_frame = Frame(root, bg='mediumturquoise', bd=4)
        low_frame.place(relx=0.20, rely=0.5, relwidth=0.35, relheight=0.4, anchor='n')
        img_frame = Frame(root, bg='mediumturquoise', bd=4)
        img_frame.place(relx=0.675, rely=0.5, relwidth=0.60, relheight=0.4, anchor='n')

    text = scrolledtext.ScrolledText(low_frame, width=200, height=200)
    text.config(state=NORMAL)
    text.pack()

    image = Text(img_frame, width=200, height=200)
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
            landsat_file = filedialog.askdirectory(initialdir=phrase, title="Select Landsat directory")
            if landsat_file == phrase:
                pass
            elif len(landsat_file) < 1:
                pass
            else:
                clear_data()
                entry_filepath.insert(END, landsat_file)
        else:
            landsat_file = filedialog.askdirectory(initialdir="C:/Users/", title="Select Landsat directory")
            if landsat_file == phrase:
                pass
            elif len(landsat_file) < 1:
                pass
            else:
                clear_data()
                entry_filepath.insert(END, landsat_file)

    def browse_roi(i):

        phrase = i

        if isdir(phrase) == True:
            roi_file = filedialog.askopenfilename(initialdir=phrase, title="Select geojson file")
            if roi_file == phrase:
                pass
            elif len(roi_file) < 1:
                pass
            else:
                clear_roi()
                entry_roi.insert(END, roi_file)

        elif isfile(phrase) == True:
            roi_file = filedialog.askopenfilename(initialdir=phrase, title="Select geojson file")
            if roi_file == phrase:
                pass
            elif len(roi_file) < 1:
                pass
            else:
                clear_roi()
                entry_roi.insert(END, roi_file)

        else:
            roi_file = filedialog.askopenfilename(initialdir="C:/Users/", title="Select geojson file")
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
            roi_batch = filedialog.askdirectory(initialdir=phrase, title="Select outpt directory")
            if roi_batch == phrase:
                pass
            elif len(roi_batch) < 1:
                pass
            else:
                clear_roi()
                entry_roi.insert(END, roi_batch)
        else:
            roi_batch = filedialog.askdirectory(initialdir="C:/Users/", title="Select outpt directory")
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
            output_file = filedialog.askdirectory(initialdir=phrase, title="Select outpt directory")
            if output_file == phrase:
                pass
            elif len(output_file) < 1:
                pass
            else:
                clear_output()
                output_path.insert(END, output_file)
        else:
            output_file = filedialog.askdirectory(initialdir="C:/Users/", title="Select outpt directory")
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
        image.image_create('1.0', image=im_resize)
        # root.image.see('1.0')
        # root.update()

    # GEOJSON/ROI FILEPATH
    entry_roi = Entry(root, font=10, bd=2)

    if boundary_filename is None:
        entry_roi.insert(END, "Water Rights Boundary")
    else:
        entry_roi.insert(END, boundary_filename)

    # entry_roi.insert(END, "C:/Users/CashOnly/Desktop/PT-JPL/ROI_477/2035.geojson")
    entry_roi['font'] = myFont
    entry_roi.place(relx=0.36, rely=0.1, relwidth=.66, relheight=0.05, anchor='n')

    roi_button = Button(root, text="Single", width=8, command=lambda: [browse_roi(get_path('Single', entry_filepath, entry_roi, output_path))])
    roi_button['font'] = myFont
    roi_button.place(relx=0.85, rely=0.1, relheight=0.05)

    roi_batch = Button(root, text="Batch", width=8, command=lambda: [browse_batch(get_path('Batch', entry_filepath, entry_roi, output_path))])
    roi_batch['font'] = myFont
    roi_batch.place(relx=0.720, rely=0.1, relheight=0.05)

    # LANDSAT DATA FILEPATH
    entry_filepath = Entry(root, font=10, bd=2, borderwidth=2)

    if input_directory is None:
        entry_filepath.insert(END, 'Landsat Directory')
    else:
        entry_filepath.insert(END, input_directory)

    # entry_filepath.insert(END, 'E:/Personal/ISC_DATA')
    entry_filepath['font'] = myFont
    entry_filepath.place(relx=0.41, rely=0.2, relwidth=.76, relheight=0.05, anchor='n')

    filepath_button = Button(root, text="Search", width=10, command=lambda: [browse_data(get_path('Landsat', entry_filepath, entry_roi, output_path))])
    filepath_button['font'] = myFont
    filepath_button.place(relx=0.825, rely=0.2, relheight=0.05)

    # OUTPUT FILEPATH
    output_path = Entry(root, font=10, bd=2)

    if output_directory is None:
        output_path.insert(END, "Output Directory")
    else:
        output_path.insert(END, output_directory)

    # output_path.insert(END, "C:/Users/CashOnly/Desktop/PT-JPL")
    output_path['font'] = myFont
    output_path.place(relx=0.41, rely=0.3, relwidth=0.76, relheight=0.05, anchor='n')

    output_button = Button(root, text="Search", width=10, command=lambda: [browse_output(get_path('Output', entry_filepath, entry_roi, output_path))])
    output_button['font'] = myFont
    output_button.place(relx=0.825, rely=0.3, relheight=0.05)

    # START YEAR
    entry_start = Entry(root, font=10, bd=2, justify='center')
    entry_start['font'] = myFont
    entry_start.place(relx=0.09, rely=0.4, relwidth=.12, relheight=0.05, anchor='n')
    # entry_start.insert(0, "2020")

    if start_year is None:
        entry_start.insert(0, "Start")
    else:
        entry_start.insert(0, start_year)

    # END YEAR
    entry_end = Entry(root, font=10, bd=2, justify='center')
    entry_end['font'] = myFont
    entry_end.place(relx=0.24, rely=0.4, relwidth=0.12, relheight=0.05, anchor='n')
    # entry_end.insert(0, "2020")

    if end_year is None:
        entry_end.insert(0, "End")
    else:
        entry_end.insert(0, end_year)

    # Clear Texts
    clear_text = Button(root, text='Clear Board', width=10, command=clear_text)
    clear_text['font'] = myFont
    clear_text.place(relx=0.825, rely=0.4, relheight=0.05)

    # SUBMIT BUTTON
    submit_button = Button(root, text="Submit", width=10, command=submit)
    submit_button['font'] = myFont
    submit_button.place(relx=0.670, rely=0.4, relheight=0.05)

    root.mainloop()
