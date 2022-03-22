import tkinter as tk 
from puzzle import AnswerError
from puzzle import Update
from puzzle import Cage

class Control(tk.Frame):
    def __init__(self, parent, win):
        tk.Frame.__init__(self, win)
        self.parent = parent
        self.bind_class('Board','<Up>', self.arrowUp)
        self.bind_class('Board','<Down>', self.arrowDown)
        self.bind_class('Board','<Left>',  self.arrowLeft)
        self.bind_class('Board','<Right>',  self.arrowRight)
        self.bind_class('Board','<ButtonPress-1>', self.onClick)
        self.bind_class('Board','<space>',  self.clearCell)
        self.bind_class('Board','u',  self.rollBack)
        self.bind_class('Board','U',  self.rollBack)
        self.bind_class('Board', 's', self.clearPuzzle)
        self.bind_class('Board', 'S', self.clearPuzzle)
        self.bind_class('Board','<Map>',  self.map)
        self.bind_class('Board','<Unmap>',  self.unmap)

        for c in range(1, 10):
            self.bind_class('Board',f'<KeyPress-{c}>',  self.toggleCandidate)
            self.bind_class('Board',f'<Control-KeyPress-{c}>',  self.enterAnswer)
            self.bind_class('Board',f'<KeyPress-KP_{c}>',  self.toggleCandidate)
            self.bind_class('Board',f'<Control-KeyPress-KP_{c}>',  self.enterAnswer)            

    def arrowUp(self, event):
        board = self.parent.board
        focus = board.focus
        if focus[1] == 0:       # already in top row
            return
        board.enterCell( (focus[0], focus[1]-1) )

    def arrowDown(self, event):
        board = self.parent.board
        focus = board.focus
        dim   = board.dim
        if focus[1] == dim-1:       # already in bottom row
            return
        board.enterCell( (focus[0], focus[1]+1) )

    def arrowLeft(self, event):
        board = self.parent.board
        focus = board.focus
        if focus[0] == 0:       # already in leftmost column
            return
        board.enterCell( (focus[0]-1, focus[1]) )

    def arrowRight(self, event):
        board = self.parent.board
        focus = board.focus
        dim   = board.dim
        if focus[0] == dim-1:       # already in rightmost column
            return
        board.enterCell( (focus[0]+1, focus[1]) )

    def enterAnswer(self, event):

        # User enters an answer in a cell.
        # Called if digit 1-dim typed with Control depressed
        # Works for top row or keypad digits

        value       = int(event.keysym[-1])
        puzzle      = self.parent.puzzle
        board       = self.parent.board
        cell        = board.focus

        if value > puzzle.dim:
            return
        
        try:
            updates = puzzle.enterAnswer(cell, value)
            board.postUpdates(updates)
            if puzzle.isCompleted():
                self.parent.timer.stop()
                board.celebrate()
        except AnswerError as x:
            board.highlight(x.cells)
        except:
            print('Error occurred')

    def toggleCandidate(self, event):
        # User toggles candidate in a cell.
        # If cell already has answer, there is no effect.
        # Called if user presses a digit (from 1 to dim) on the top row
        # Otherwise, toogles the candidate value from off to on, or vice-versa.

        value  = int(event.char)
        puzzle = self.parent.puzzle
        board  = self.parent.board
        cell   = board.focus


        if value > puzzle.dim:
            return

        updates = puzzle.toggleCandidate(cell, value)
        board.postUpdates(updates)

    def onClick(self, event):
        board = self.parent.board
        board.shiftFocus(event.x, event.y)

    def clearCell(self, event):
        # User types space bar
        # If candidates are displayed, clear all candidates for current cell.
        # If there is an answer in the cell, delete it and display the
        # cell's candidates instead.

        puzzle = self.parent.puzzle
        board  = self.parent.board
        cell   = board.focus

        updates = puzzle.clearCell(cell)
        board.postUpdates(updates)

    def rollBack(self, event):
        # Undo history until checkpoint is encountered.

        updates = self.parent.puzzle.undo()
        self.parent.board.postUpdates(updates)

    def map(self, event):
        timer = self.parent.timer
        if timer.state == 'paused':
            timer.resume()

    def unmap(self, event):
        timer = self.parent.timer
        if timer.state == 'running':
            timer.pause()

    def getCages(self):
        # Get a list of the cages from the puzzle.

        for cage in self.parent.puzzle.cages.values():
            yield cage

    def getEntries(self):
        # Get a list of all entries from the puzzle.

        return self.parent.puzzle.getAllEntries()

    def getTime(self):
        return self.parent.timer.time()

    def setTime(self, seconds):
        self.parent.timer.setTime(seconds)

    def clearPuzzle(self, event):
        # Start current puzzle over
        # Do not reset the timer

        puzzle = self.parent.puzzle
        board  = self.parent.board

        puzzle.restart()
        updates = puzzle.getAllEntries()
        board.restart(updates)
