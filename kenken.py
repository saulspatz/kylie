#! /usr/bin/python
''' Graphic user interface for kenken puzzle. 
'''
import tkinter as tk
from subprocess import run

from control   import Control
from board     import Board
from puzzle import Puzzle
from stopwatch import StopWatch
                                      
class KenKen(object):            
    def __init__(self, win, height = 1020, width = 1200, cursor = 'crosshair', bg = 'white'):    
        self.win = win
        self.win.title('KenKen')
        icon = tk.Image('photo', file='kenken.png')
        win.tk.call('wm', 'iconphoto', win._w, icon)
        win.resizable(False, False)        
        self.control = Control(self, win)                
        self.board = Board(self, win, dim = 9, height = height, width = width, bg = bg, cursor=cursor)
        self.timer = StopWatch(win)
        self.timer.pack()
        self.board.pack(side = tk.TOP, expand=tk.YES, fill=tk.BOTH)
        dim = 9
        diff = 'x'
        self.newPuzzle(dim, diff)  # sets self.puzzle

    def newPuzzle(self, dim, diff):
        c = run(['./keen', '--generate', '1', f'{dim}d{diff}'], capture_output=True)
        code = c.stdout.decode()
        with open('code.txt', 'a') as fin:
            fin.write(code)
        self.puzzle = Puzzle(self, code)
        self.board.draw(dim)
        self.timer.start()
                    
def main():
    root = tk.Tk()                             
    KenKen(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
                
            
            
        