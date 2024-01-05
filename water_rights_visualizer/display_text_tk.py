import io
from tkinter import Tk
from tkinter.scrolledtext import ScrolledText

def display_text_tk(text: str, text_panel: ScrolledText, root: Tk) -> str:
    """
    Display the given text in the text_panel using Tkinter.

    Args:
        text (str): The text to be displayed.
        text_panel (ScrolledText): The ScrolledText widget where the text will be displayed.
        root (Tk): The root Tkinter window.

    Returns:
        str: The string "break".
    """
    # Create a StringIO object to hold the text
    display_text = io.StringIO(f"{text}")
    # Get the value of the StringIO object as a string
    output = display_text.getvalue()
    # Insert the text into the text_panel at the beginning
    text_panel.insert('1.0', output)
    # Update the Tkinter window to reflect the changes
    root.update()

    return "break"
