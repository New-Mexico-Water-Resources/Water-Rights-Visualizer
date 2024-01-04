import io
from tkinter import Tk
from tkinter.scrolledtext import ScrolledText


def display_text_tk(text: str, text_panel: ScrolledText, root: Tk) -> str:
    display_text = io.StringIO(f"{text}")
    output = display_text.getvalue()
    text_panel.insert('1.0', output)
    root.update()

    return "break"
