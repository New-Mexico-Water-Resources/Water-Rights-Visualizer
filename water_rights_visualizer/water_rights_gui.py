import logging
import sys
from os.path import isfile, isdir, abspath, join, dirname, exists
from tkinter import Tk, Canvas, font as font, PhotoImage, Label, Frame, scrolledtext, NORMAL, Text, filedialog, END, Entry, Button

import PIL.Image
import PIL.ImageTk

from .get_path import get_path
from .submit_button_tk import submit_button_tk

logger = logging.getLogger(__name__)


def water_rights_gui(
        boundary_filename: str,
        output_directory: str,
        input_directory: str,
        start_year: str,
        end_year: str):
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

    text_panel = scrolledtext.ScrolledText(low_frame, width=200, height=200)
    text_panel.config(state=NORMAL)
    text_panel.pack()

    image_panel = Text(img_frame, width=200, height=200)
    image_panel.config(state=NORMAL)
    image_panel.pack()

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
        image_panel.delete(1.0, END)
        text_panel.delete(1.0, END)
        progress.set(0)
        root.update()

    # def add_image(filename):
    #     global im_resize
    #     logger.info(f"opening image_panel: {filename}")
    #     im = PIL.Image.open(filename)
    #     im = im.resize((375, 225), PIL.Image.BICUBIC)
    #     im_resize = PIL.ImageTk.PhotoImage(im)
    #     image_panel.image_create('1.0', image_panel=im_resize)

    # GEOJSON/ROI FILEPATH
    entry_roi = Entry(root, font=10, bd=2)

    if boundary_filename is None:
        entry_roi.insert(END, "Water Rights Boundary")
    else:
        entry_roi.insert(END, boundary_filename)

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
    clear_text = Button(root, text='Clear Board', width=10, command=lambda: clear_text())
    clear_text['font'] = myFont
    clear_text.place(relx=0.825, rely=0.4, relheight=0.05)

    # SUBMIT BUTTON
    submit_button = Button(root, text="Submit", width=10, command=lambda: submit_button_tk(root, text_panel, image_panel, entry_filepath, entry_roi, entry_start, entry_end, output_path))
    submit_button['font'] = myFont
    submit_button.place(relx=0.670, rely=0.4, relheight=0.05)

    root.mainloop()
