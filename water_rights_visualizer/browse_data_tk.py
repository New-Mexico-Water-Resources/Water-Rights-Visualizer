def browse_data(clear_data, entry_filepath, i):

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