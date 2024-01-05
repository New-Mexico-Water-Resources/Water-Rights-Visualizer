def browse_output(clear_output, output_path, i):

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