import tkinter as tk
from tkinter import font
import time

ADD = '+'
SUB = '\u2212'
MUL = '\xd7'
DIV = '/'

operation = [ADD, SUB, MUL, DIV]
clueSize = 16
solutionSize = 36
candidateSize = 20

baseHeight = 1020
baseWidth = 1200


# cageColor = ('#FFDCA0', '#F0C8C8', '#DCFFFF', '#C4C4FF', '#E5D6B4', '#D6ED84')
cageColor = ('cornflower blue',
             'dodger blue',
             'deep sky blue',
             'royal blue',
             'steel blue',
             'cyan3',)


class Board(tk.Canvas):
    # View

    def __init__(self, parent, win, height=baseHeight, width=baseWidth,
                 bg='white', dim=9, cursor='crosshair'):
        tk.Canvas.__init__(self, win, height=height, width=width,
                           bg=bg, cursor=cursor)
        self.parent = parent
        self.clueFont = font.Font(
            family='JetBrains Mono', size=clueSize, weight='bold')
        self.solutionFont = font.Font(
            family='JetBrains Mono', size=solutionSize, weight='bold')
        self.candidateFont = font.Font(
            family='JetBrains Mono', size=candidateSize, weight='bold')

    def draw(self, dim):
        self.bind('<Configure>', self.redraw)
        width = self.winfo_width()
        height = self.winfo_height()
        self.dim = dim
        self.createCells(height, width)
        control = self.parent.control
        for cage in control.getCages():
            self.drawCage(cage)
        self.current = (0, 0)
        self.enterCell((0, 0))         # initial focus in upper lefthand corner
        self.focus_set()              # make canvas respond to keystrokes
        self.activate()               # activate event bindings

    def redraw(self, event):
        self.clearAll()
        self.createCells(event.height, event.width)
        control = self.parent.control
        for cage in control.getCages():
            self.drawCage(cage)
        updates = control.getEntries()
        for update in updates:
            self.postUpdate(update)
        try:
            self.enterCell(self.current)
        except (AttributeError, TypeError):
            pass

    def createCells(self, height, width):
        dim = self.dim
        self.cellWidth = cw = (width - 10) // dim
        self.cellHeight = ch = (height - 10) // dim
        # cell origin is (x0, y0)
        x0 = self.x0 = (width - dim * cw) // 2
        y0 = self.y0 = (height - dim * ch) // 2

        for j, x in enumerate(range(self.x0, self.x0+dim*cw, cw)):
            for k, y in enumerate(range(self.y0,  self.y0+dim*ch, ch)):
                tag = 'rect%d%d' % (j, k)
                self.create_rectangle(x, y, x + cw, y + ch, tag=tag)
        self.create_polygon(x0, y0+ch//2, x0+cw//4, y0+3*ch//4, x0, y0+ch,
                            fill='khaki3', tag='cursor')

    def drawCage(self, cage):
        x0 = self.x0
        y0 = self.y0
        ch = self.cellHeight
        cw = self.cellWidth
        op = cage.op
        value = cage.value
        bground = cageColor[cage.color]

        for (j, k) in cage:
            self.itemconfigure('rect%d%d' % (j, k), fill=bground)
            w = x0 + j*cw
            e = w + cw
            n = y0 + k*ch
            s = n + ch
            if (j-1, k) not in cage:
                self.create_line(w, n, w, s, width=3,
                                 fill='black')  # western bdry
            if (j+1, k) not in cage:
                self.create_line(e, n, e,  s, width=3,
                                 fill='black')  # eastern bdry
            if (j, k-1) not in cage:
                self.create_line(w, n, e, n, width=3,
                                 fill='black')   # northern bdry
            if (j, k+1) not in cage:
                self.create_line(w, s, e, s, width=3,
                                 fill='black')    # southern bdry
            atag = 'a%d%d' % (j, k)
            ctag = 'c%d%d' % (j, k)
            x = (e + w) // 2
            y = (n + s) // 2
            self.create_text(x, y, text='', font=self.solutionFont, anchor=tk.CENTER,
                             tag=atag, fill='black')
            self.addtag_withtag('atext', atag)
            x = e - 5
            y = n + 2
            self.create_text(x, y, text='', font=self.candidateFont, tag=ctag,
                             anchor=tk.NE, justify=tk.LEFT, fill='black')
            self.addtag_withtag('ctext', ctag)

        # formula in upper lefthand corner

        kmin = min([k for (j, k) in cage])
        jmin = min([j for(j, k) in cage if k == kmin])
        j, k = x0+cw*jmin+4, y0 + ch*kmin+5
        self.create_text(j, k, text='%s%s' % (value, op),
                         font=self.clueFont, anchor=tk.NW, fill='black', tag='formula')

    def clearAll(self):
        objects = self.find_all()
        for object in objects:
            self.delete(object)

    def flash(self, rects, num):
        if num == 0:
            # switch to bg color in case we missed an event
            for tag, bg, color in rects:
                self.itemconfigure(tag, fill=bg)
            self.update_idletasks()
            return
        for tag, bg, color in rects:
            col = bg if num % 2 else color
            self.itemconfigure(tag, fill=col)
        self.update_idletasks()
        self.after(100, lambda: self.flash(rects, num-1))

    def highlight(self, cells, color='yellow', num = 2):
        # Flash given cells in the given highlight color, num times
        # It is assumed that the highlight color will never be the
        # background color of a cell.  
        # Record the original background colors of the cells, so as 
        # to be able to restore them, then call flash.

        rects = []
        for cell in cells:
            tag = 'rect%d%d' % cell
            bg = self.itemcget(tag, 'fill')
            rects.append((tag, bg, color))
        self.flash(rects, 2*num)

    def candidateString(self, cands):
        # String representation of a list of candidates

        if not cands:
            return ''
        string = ''.join(
            [str(x) if x in cands else ' ' for x in range(1, 1+self.dim)])
        return string[:3] + '\n' + string[3:6] + '\n' + string[6:]

    def enterCell(self, cell):
        # Cell is (col, row) pair
        # Give focus to cell
        # Sets self.current

        tag = 'rect%d%d' % cell
        old = self.current
        deltaX = (cell[0] - old[0])*self.cellWidth
        deltaY = (cell[1] - old[1])*self.cellHeight

        self.current = cell
        self.move('cursor', deltaX, deltaY)

    def postUpdate(self, update):
        if not update:
            return

        coords = update.coords
        cands = update.candidates
        answer = update.answer
        atag = 'a%d%d' % coords
        ctag = 'c%d%d' % coords

        if answer:
            self.itemconfigure(ctag, text='')
            self.itemconfigure(atag, text=str(answer))
        else:
            self.itemconfigure(ctag, text=self.candidateString(cands))
            self.itemconfigure(atag, text='')

    def undo(self, update):
        self.postUpdate(update)
        self.enterCell(update.coords)
        self.itemconfigure('cursor', state=tk.NORMAL)

    def redo(self, update):
        self.postUpdate(update)
        self.enterCell(update.coords)
        if self.parent.puzzle.isCompleted():
            self.itemconfigure('cursor', state=tk.HIDDEN)

    def shiftFocus(self, x, y):
        # User clicked the point (x, y)

        j = (x - self.x0) // self.cellWidth
        if not 0 <= j < self.dim:
            return
        k = (y - self.y0) // self.cellHeight
        if not 0 <= k < self.dim:
            return
        self.enterCell((j, k))

    def celebrate(self):
        # Indicate a win by flashing board green
        # Drop the focus

        all = [(x, y) for x in range(self.dim) for y in range(self.dim)]
        self.itemconfigure('cursor', state=tk.HIDDEN)
        self.highlight(all, 'green', 4)

    def restart(self):
        # Clear all solution data from the board
        # User wants to start current puzzle over

        self.itemconfigure('cursor', state=tk.NORMAL)
        self.itemconfigure('atext', text='')
        cstr = self.candidateString([])
        self.itemconfigure('ctext', text=cstr)
        self.enterCell((0, 0))
        self.activate()

    def deactivate(self):
        # Replace the 'Board' bindatg by 'Canvas'.
        # See defininition of Control in control.py
        # Board will no longer respond to keypresses and mouseclicks

        tags = self.bindtags()
        tags = (tags[0], 'Canvas') + tags[2:]
        self.bindtags(tags)

    def activate(self):
        # Activate event bindings
        # Reverse of deactivate, above

        tags = self.bindtags()
        tags = (tags[0], 'Board') + tags[2:]
        self.bindtags(tags)
