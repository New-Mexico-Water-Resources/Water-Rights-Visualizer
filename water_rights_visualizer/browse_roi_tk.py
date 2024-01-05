def browse_roi(clear_roi, entry_roi, i):

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