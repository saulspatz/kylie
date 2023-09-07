#! /usr/bin/python3
''' Graphic user interface for kenken puzzle. 
'''
import tkinter as tk
from tkinter import filedialog
from subprocess import run

from control   import Control
from board     import Board
from puzzle import Puzzle
from stopwatch import StopWatch
from dialogs import PopUp
                                      
class KenKen(object):            
    def __init__(self, win, height = 1020, width = 1200, cursor = 'crosshair', bg = 'white'):    
        self.win = win
        self.win.title('KenKen')
        icon = tk.Image('photo', file='kenken.png')
        win.tk.call('wm', 'iconphoto', win._w, icon)
        win.resizable(False, False)   
        self.difficulty = tk.IntVar(self)  # used in the Settings dialog 
        self.dimension = tk.IntVar(self)     
        self.control = Control(self, win)                
        self.board = Board(self, win, dim = 9, height = height, width = width, bg = bg, cursor=cursor)
        self.timer = StopWatch(win)
        self.timer.pack()
        self.board.pack(side = tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.fileSizes = self.getFileSizes()
        self.settings = PopUp()
        self.settings.withdraw()
        self.newPuzzle()  # sets self.puzzle

    def newPuzzle(self, dim=9, diff='x'):
        #c = run(['./keen', '--generate', '1', f'{dim}d{diff}'], capture_output=True)
        code = c.stdout.decode()
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
        for diff in ('easy', 'normal', 'hard', 'extreme'):
            for dim in range(6,10):
                with open(f'keys/{diff}{dim}.txt') as fin:
                    for count, _ in enumerate(fin):
                        pass
                sizes[diff,dim] = count+1
        return sizes


                    
def main():
    root = tk.Tk()                             
    KenKen(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
                
            
            
        