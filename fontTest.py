import tkinter as tk
import tkinter.font as tkFont


master = tk.Tk()
my_font = tkFont.Font(size=10)
def resizer(event):
    if event.width in range(300,325):
        my_font.configure(size=10)   
    elif event.width in range(400,425):
        my_font.configure(size=20)
    elif event.width > 600:
        my_font.configure(size=30)


a_label= tk.Label(font=my_font, text="Welcome")
a_label.grid()
an_entry = tk.Entry(font=my_font)
an_entry.grid()
an_entry.insert(0,'some text')
master.bind("<Configure>", resizer)
tk.mainloop()
