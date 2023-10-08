#! /usr/bin/python3
''' Graphic user interface for kenken puzzle. 
'''
import tkinter as tk
import linecache
from tkinter import filedialog
from random import randrange

from control   import Control
from board     import Board
from puzzle import Puzzle
from stopwatch import StopWatch
from dialogs import PopUp
                                      
class KenKen(tk.Frame):             
    def __init__(self, win):
        super().__init__(win, height = 1020, width = 1200, cursor = 'crosshair', bg = 'white')  
        self.win = win
        self.win.title('KenKen')
        icon = tk.Image('photo', file='kenken.png')
        win.tk.call('wm', 'iconphoto', win._w, icon)
        win.resizable(False, False)   
        self.difficulty = tk.IntVar(self)  # used in the Settings dialog 
        self.dimension = tk.IntVar(self)
        self.difficulty.set(0)
        self.dimension.set(0)
        self.levels = 'easy', 'normal', 'hard', 'extreme'
        self.control = Control(self, win)
                     
        self.timer = StopWatch(win)
        self.timer.pack()
        self.board.pack(side = tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.fileSizes = self.getFileSizes()
        self.grid()
        self.newPuzzle()  # sets self.puzzle
        self.settings = PopUp(self)

    def newPuzzle(self):
        diff = self.difficulty.get()
        dim = self.dimension.get()
        self.board = Board(self, self.win, dim = dim, height = height, width = width, bg = bg, cursor=cursor)
        fn = f'keys/{diff}{dim}.txt'
        size = self.fileSizes[diff, dim]
        idx = randrange(size)
        code = linecache.getline(fn, idx)
        with open('code.txt', 'w') as fin:
            fin.write(code)
        self.puzzleFromCode(code)
        
    def openPuzzle(self):
        fn = filedialog.askopenfilename(parent=self.win,
                                        title='Open Saved Puzzle',
                                        initialdir='.',
                                        filetypes=[('TXT','*.txt')])
        if not fn:
            return
        code = open(fn).read()
        self.puzzleFromCode(code)
        
    def puzzleFromCode(self, code):
        dim = int(code[0])
        self.puzzle = Puzzle(self, code)
        self.board.draw(dim)
        self.timer.start()

    def getFileSizes(self):
        sizes = {}
        for diff in self.levels:
            for dim in range(6,10):
                with open(f'keys/{diff}{dim}.txt') as fin:
                    for count, _ in enumerate(fin):
                        pass
                sizes[diff,dim] = count+1
        return sizes

def main():
    root = tk.Tk()
    app = KenKen(root)
    app.mainloop()
    
if __name__ == "__main__":
    main()
                
            
            
        