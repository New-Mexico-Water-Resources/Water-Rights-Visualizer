def browse_batch(clear_roi, entry_roi, i):

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