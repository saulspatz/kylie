# puzzle.py
from subprocess import run
import re
from collections import defaultdict
from itertools import combinations

ADD = 0
SUB = 1
MUL = 2
DIV = 3

class AnswerError(Exception):
    def __init__(self, cells):
        self.cells = cells

class Cage():
    def __init__(self, op, val, cells):
        self.cells = cells
        self.op = op
        self.value = val
        self.color = None
    
    def __str__(self):
        return f'{sorted(self.cells)} {self.value}{"+-*/"[self.op]}'
    
    def touch(self, other):
        other = other.cells
        for cell in self.cells:
            x,y = cell
            if (x,y+1) in other: return True
            if (x,y-1) in other: return True
            if (x-1, y) in other: return True
            if (x+1, y) in other: return True
        return False 

class Update(object):
    def __init__(self, coords, ans, cand):
        self.coords, self.answer, self.candidates = coords, ans, cand

class Puzzle(object):            
    def __init__(self, codeString):
        self.code = codeString
        self.dim = dim = int(codeString[0])
        self.cages        = {}
        self.history      = []
        self.answer       = {}
        self.candidates   = defaultdict(list)
        self.cageID       = {}     # map cell to its cage
        self.future       = []

        self.makeCages(codeString)

        for x in range(dim):
            for y in range(dim):
                self.answer[x,y] = 0  #impossible value
 
    def makeCages(self, codeString):
        # Convert the cages codes from Tatham's representation.    
        dim = self.dim
        cageCode, operCode = codeString[2:].split(',')
        pattern = re.compile(r'[_abcdefghijklm]|[0-9]+')
        groups = pattern.findall(cageCode)
        symbols = '_abcdefghijklm'
        code = ''
        for group in groups:
            if group in symbols:
                code += group
            else:
                code += (int(group)-1)*code[-1]
        code = [symbols.index(c) for c in code]
        blocks = defaultdict(set)
        for row in range(dim):
            for col in range(dim):
                blocks[row,col].add((row, col))
        cursor = 0
        for c in code:
            while c:
                c -=1
                if cursor < dim*(dim-1): 
                    #vertical edge
                    row = cursor//(dim-1) 
                    col = cursor%(dim-1)   
                    p0 =  row, col
                    p1 =  row, col+1
                else:
                    #horizontal edge
                    col = cursor//(dim-1)-dim 
                    row = cursor%(dim-1) + 1
                    p0 = row-1, col
                    p1 = row, col
                union = blocks[p0] | blocks[p1]
                for cell in union:
                    blocks[cell] = union
                cursor += 1
            cursor += 1
        # ************************ TODO ********************
        # Need to find connected components from blocks  *
        # **************************************************
        cages = {}
        cages = {b:blocks[b] for b in blocks if b== min(blocks[b])}
        pattern =re.compile(r'[adms][0-9]+')
        clues = pattern.findall(operCode)
        try:
            assert len(cages) == len(clues)
        except:
            print(codeString)
            for item in cages.items():
                print(item)
        for id, clue  in zip(sorted(cages), clues):
            cells = cages[id]
            for cell in cells:
                self.cageID[cell] = id
            op = 'asmd'.index(clue[0])
            answer = int(clue[1:])
            self.cages[id] = Cage(op, answer, cells)
        self.colorCages()

    def colorCages(self):
        # Color the cells with at most 6 colors
        cages = self.cages
        def color6(graph): 
            if len(graph)== 1:
                id = list(graph.keys())[0]
                cages[id].color = 0
                return
            for id in graph:   # The must be a vertex of degree <= 5
                if len(graph[id]) < 6:
                    break
            nbrs = graph.pop(id)  # remove it from the graph
            for nbr in nbrs:
                graph[nbr].remove(id)
            
            # 6-color the reamining graph, then color the
            # deleted vertex with a color unused by its neighbors
             
            color6(graph)       
            nbdColors = {cages[n].color for n in nbrs}
            color = min(set(range(6))-nbdColors)
            cages[id].color = color

        adj = defaultdict(set)
        for u,v in combinations(cages.keys(), 2):
            if cages[v].touch(cages[u]):
                adj[u].add(v)
                adj[v].add(u)
        color6(adj)
        
      
    def enterAnswer(self, focus, value):
        
        # User enters an answer in a cell.

        # If the answer conflicts with a value already entered in another cell, 
        # or this answer completes a cage, and the arithmetic is wrong,
        # raise AnswerError.
        
        # If the user is simply reentering the same answer in a cell, do nothing
        # and return None.

        # Otherwise, return the update
        
        dim, answer = self.dim, self.answer
        
        if answer[focus] == value:
            return None
        
        row = [x for x in range(dim) if answer[(x, focus[1])] == value]
        col = [y for y in range(dim) if answer[(focus[0], y)] == value]
        cells = [(x, focus[1]) for x in row] + [(focus[0], y) for y in col]
        
        if cells:
            raise AnswerError(cells)
        
        id = self.cageID[focus]
        cage = self.cages[id]
        cells = cage.cells
        
        if len([x for x in cells if x != focus and answer[x]]) == len(cells) - 1:
            if not self.goodAnswer(cage, focus, value):
                raise AnswerError(cells)
        answer[focus] = value
        update = self.update(focus)
        self.history.append(update)
        self.future = []
        return update
                
    def update(self, focus):
        return Update(focus, self.answer[focus], self.candidates[focus][:])
        
    def toggleCandidate(self, focus, value):
        # Ignore if answer already in focus cell.
        # Otherwise, toggle the candidate value on or off.
                
        # Enter transaction in history and return a list of updates
        
        history, dim, answer, candidates = \
               self.history, self.dim, self.answer, self.candidates
        
        if answer[focus]:                         # answer present
            return None
                         
        if value in candidates[focus]:            # toggle value off
            candidates[focus].remove(value)
        else:
            candidates[focus].append(value)  
        update = self.update(focus)
        history.append(update)      
        return update                         
        
    def undo(self):
        # Undo last update if any
        
        answer, candidates, history = self.answer, self.candidates, self.history
        try:
            update = history.pop()
        except IndexError:                    # user tried one too many undos
            return None

        self.future.append(update)
        coords             = update.coords
        answer[coords]     = update.answer
        candidates[coords] = update.candidates
        return update

    def redo(self):
        # Redo last undo if any
        
        answer, candidates, future = self.answer, self.candidates, self.future
        try:
            update = future.pop()
        except IndexError:                    # user tried one too many redos
            return None

        self.history.append(update)
        coords             = update.coords
        answer[coords]     = update.answer
        candidates[coords] = update.candidates
        return update
    
    def clearCell(self, focus):
        # If there is an answer in the current cell clear it.
        # If there is no answer, clear the candidate list.
        # Return the update
        
        answer, candidates, history = self.answer, self.candidates, self.history
        if not answer[focus] and not candidates[focus]:
            return None                                # nothing to clear
             
        if answer[focus]:
            answer[focus] = 0
        else:
            candidates[focus] = []
        update = self.update(focus)
        history.append(update) 
        return update
    
    def isCompleted(self):
        # Has user entered answer in each cell?
        
        if len([x for x in list(self.answer.values()) if x]) == self.dim ** 2:
            return True
        else:
            return False
            
    def goodAnswer(self, cage, focus, value):
        # Precondition: Evey cell in cage, except focus, has an answer filled in
        # Return true iff filling value into focus makes the
        # arithmetic work out        

        operands = [self.answer[x] for x in cage.cells if x != focus]
        operands += [value]
        if cage.op == ADD:
            return sum(operands) == cage.value
        if cage.op == SUB:
            return max(operands) - min(operands) == cage.value
        if cage.op == MUL:
            product = 1
            for x in operands:
                product *= x
            return product == cage.value
        if cage.op == DIV:
            return max(operands) // min(operands) == cage.value

    def entries(self):
        # Return a list of updates for all cell that have a value (answer or candidate).
        # Used for redrawing the board.
        
        dim = self.dim
        answer, candidates = self.answer, self.candidates
        updates = []
        for j in range(dim):
            for k in range(dim):
                if answer[(j, k)] or candidates[(j, k)]:
                    updates.append(self.foculs( (j, k) ))
        return updates   
           
if __name__ == '__main__':  
    #     
    # Use Simon Tatham program to generate extreme 9x9 puzzle
    # 
    codeString = "9:a_aa_a_a_3a_5a_5b_5aa_9a__a_a3ba3__a_a_3a_a3b_3ab_3aa_3a3__a__a_a_3a_a__a_a,s2d4a8m24s5a9a8a10m24s5m5a13s3d2d2s3s1m18m8m45m96m72a10a13d2a13s1m45s2d2s4d2a14m108a13s1s4"
    puzzle = Puzzle(codeString)


    
