import logging
import sys
from os.path import isfile, isdir, abspath, join, dirname, exists
from tkinter import Tk, Canvas, font as font, PhotoImage, Label, Frame, scrolledtext, NORMAL, Text, filedialog, END, \
    Entry, Button

import PIL.Image
import PIL.ImageTk

from .constants import CANVAS_HEIGHT_TK, CANVAS_WIDTH_TK
from .browse_batch_tk import browse_batch
from .browse_data_tk import browse_data
from .browse_output_tk import browse_output
from .browse_roi_tk import browse_roi
from .get_path import get_path
from .submit_button_tk import submit_button_tk

logger = logging.getLogger(__name__)

def water_rights_gui_tk(
        boundary_filename: str,
        output_directory: str,
        input_directory: str,
        start_year: str,
        end_year: str):
    root = Tk()
    root.title("JPL-NMOSE ET visualizer")
    root.geometry("700x600")
    root.resizable(0, 0)
    canvas = Canvas(root, height=CANVAS_HEIGHT_TK, width=CANVAS_WIDTH_TK)
    canvas.pack()
    myFont = font.Font(family='Helvetica', size=12)
    imgpath = join(dirname(abspath(sys.argv[0])), "img4.png")

    if exists(imgpath):
        label_color = 'skyblue'
        frame_color = 'skyblue'
        img = PhotoImage(file=imgpath)
    else:
        label_color = 'lightseagreen'
        frame_color = 'mediumturquoise'
        img = None
    
    background_label = Label(root, image=img, bg=label_color)
    background_label.place(relwidth=1, relheight=1)

    low_frame = Frame(root, bg=frame_color, bd=4)
    low_frame.place(relx=0.20, rely=0.5, relwidth=0.35, relheight=0.4, anchor='n')

    img_frame = Frame(root, bg=frame_color, bd=4)
    img_frame.place(relx=0.675, rely=0.5, relwidth=0.60, relheight=0.4, anchor='n')

    text_panel = scrolledtext.ScrolledText(low_frame, width=200, height=200)
    text_panel.config(state=NORMAL)
    text_panel.pack()

    image_panel = Text(img_frame, width=200, height=200)
    image_panel.config(state=NORMAL)
    image_panel.pack()

    def clear_roi():
        entry_roi.delete(0, 'end')

    def clear_data():
        entry_filepath.delete(0, 'end')

    def clear_output():
        output_path.delete(0, 'end')

    def clear_text():
        image_panel.delete(1.0, END)
        text_panel.delete(1.0, END)
        root.update()

    # GEOJSON/ROI FILEPATH
    entry_roi = Entry(root, font=10, bd=2)

    if boundary_filename is None:
        entry_roi.insert(END, "Water Rights Boundary")
    else:
        entry_roi.insert(END, boundary_filename)

    entry_roi['font'] = myFont
    entry_roi.place(relx=0.36, rely=0.1, relwidth=.66, relheight=0.05, anchor='n')

    roi_button = Button(root, text="Single", width=8, command=lambda: [browse_roi(clear_roi, entry_roi,
                                                                                  get_path('Single', entry_filepath,
                                                                                           entry_roi, output_path))])
    roi_button['font'] = myFont
    roi_button.place(relx=0.85, rely=0.1, relheight=0.05)

    roi_batch = Button(root, text="Batch", width=8, command=lambda: [browse_batch(clear_roi, entry_roi,
                                                                                  get_path('Batch', entry_filepath,
                                                                                           entry_roi, output_path))])
    roi_batch['font'] = myFont
    roi_batch.place(relx=0.720, rely=0.1, relheight=0.05)

    # LANDSAT DATA FILEPATH
    entry_filepath = Entry(root, font=10, bd=2, borderwidth=2)

    if input_directory is None:
        entry_filepath.insert(END, 'Landsat Directory')
    else:
        entry_filepath.insert(END, input_directory)

    entry_filepath['font'] = myFont
    entry_filepath.place(relx=0.41, rely=0.2, relwidth=.76, relheight=0.05, anchor='n')

    filepath_button = Button(root, text="Search", width=10, command=lambda: [browse_data(clear_data, entry_filepath,
                                                                                         get_path('Landsat',
                                                                                                  entry_filepath,
                                                                                                  entry_roi,
                                                                                                  output_path))])
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

    output_button = Button(root, text="Search", width=10, command=lambda: [browse_output(clear_output, output_path,
                                                                                         get_path('Output',
                                                                                                  entry_filepath,
                                                                                                  entry_roi,
                                                                                                  output_path))])
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
    submit_button = Button(root, text="Submit", width=10,
                           command=lambda: submit_button_tk(root, text_panel, image_panel, entry_filepath, entry_roi,
                                                            entry_start, entry_end, output_path))
    submit_button['font'] = myFont
    submit_button.place(relx=0.670, rely=0.4, relheight=0.05)

    root.mainloop()

def main(argv=sys.argv):
    if "--boundary-filename" in argv:
        boundary_filename = str(argv[argv.index("--boundary-filename") + 1])
    else:
        boundary_filename = None

    if "--output-directory" in argv:
        output_directory = str(argv[argv.index("--output-directory") + 1])
    else:
        output_directory = None

    if "--input-directory" in argv:
        input_directory = str(argv[argv.index("--input-directory") + 1])
    else:
        input_directory = None

    if "--start-year" in argv:
        start_year = str(argv[argv.index("--start-year") + 1])
    else:
        start_year = None

    if "--end-year" in argv:
        end_year = str(argv[argv.index("--end-year") + 1])
    else:
        end_year = None

    water_rights_gui_tk(
        boundary_filename=boundary_filename,
        output_directory=output_directory,
        input_directory=input_directory,
        start_year=start_year,
        end_year=end_year
    )

if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))