import tkinter as tk
from tkinter import simpledialog

class PopUp(simpledialog.Dialog):
    def __init__(self, parent, title):
        self.parent = parent 
        super().__init__(parent, title)

    class RadioBox(tk.LabelFrame):
        def __init__(self, master, title, values, var):
            super().__init__(master, text= title, labelanchor=tk.N)  
            for idx, val in enumerate(values):
                button = tk.Radiobutton(self, variable=var, text = val, value = idx)
                button.grid(row= idx, column = 0, sticky = tk.W)
                      
    def body(self, frame):
        parent = self.parent
        rb1 = self.RadioBox(frame, 'Difficulty', 
            ('Easy', 'Normal', 'Hard', 'Extreme'), parent.difficulty)
        rb2 = self.RadioBox(frame, 'Dimension', 
            ('6', '7', '8', '9'), parent.dimension)
        rb1.grid(row = 0, column = 0)
        rb2.grid(row = 0, column = 1)
        return frame
        
root = tk.Tk()
root.difficulty = tk.IntVar(root)
root.dimension = tk.IntVar(root)
PopUp(root, 'Settings')
root.mainloop()