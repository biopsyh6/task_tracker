from tkinter import Tk
from smart_assistant import SmartAssistantGUI

def run_gui():
    root = Tk()
    app = SmartAssistantGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()