''' Graphic user interface for kenken puzzle client.
'''

import tkinter as  tk
import  os, re
from subprocess import run

from control   import Control
from board     import Board
from newpuzzle import Puzzle
from stopwatch import StopWatch
        
                                       
class KenKen(object):            
    def __init__(self, win, height = 600, width = 600, cursor = 'crosshair', bg = 'white'):    
        self.win = win
        self.win.title('KenKen')        
        self.control = Control(self, win)                
        self.board = Board(self, win, dim = 9, height = height, width = width, bg = bg, cursor=cursor)
        self.timer = StopWatch(win)
        self.timer.pack()
        self.board.pack(side = tk.TOP, expand=tk.YES, fill=tk.BOTH)
        dim = 9
        self.newPuzzle(dim)  # sets self.puzzle

    def newPuzzle(self, dim):
        dim = 9
        c = run(['./keen', '--generate', '1', f'{dim}dx'], capture_output=True)
        code = c.stdout.decode()
        self.puzzle = Puzzle(self, code)
        self.board.draw(dim)
        self.timer.start()
        # self.board.bind('<Configure>', self.board.redraw)

                    
def main():
    root = tk.Tk()                             
    KenKen(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
                
            
            
        