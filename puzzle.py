from collections import defaultdict, namedtuple
from itertools import combinations
import re
import os
from subprocess import run

ADD = '+'
SUB = '\u2212'
MUL ='\xd7'
DIV = '/'
operation = [ADD, SUB, MUL, DIV]

Update = namedtuple('Update', ['coords', 'answer', 'candidates']) 
class AnswerError(Exception):
    def __init__(self, cage):
        self.cells = cage
                
class Cage(list):
    def __init__(self, op, val, cells):
        self.op = op
        self.value = val
        self.color = None
        for c in cells:
            self.append( (int(c[0]), int(c[1])) )
    
    def __str__(self):
        answer = '%s %s %s' %(self.op, str(self.value), '[ ')
        for cell in sorted(self):
            answer = answer + "%d%d " % (cell[0], cell[1])
        answer = answer + ( '] %d' % self.color )   
        return answer

    def touch(self, other):
        for cell in self:
            x,y = cell
            if (x,y+1) in other: return True
            if (x,y-1) in other: return True
            if (x-1, y) in other: return True
            if (x+1, y) in other: return True
        return False
            
class Journal(object):
    def __init__(self, coords, before, after):
        self.coords = coords
        self.b_ans = before[0]
        self.b_cand = before[1]
        self.a_ans = after[0]
        self.a_cand = after[1]
    def __str__(self):
        return f'{self.coords} before: {self.b.ans} {self.b.cand} after: {self.a.ans} {self.a.cand}'

class Puzzle(object):            
    def __init__(self, parent, codeString):
        self.code = codeString
        self.dim = dim = int(codeString[0])
        self.cages        = {}
        self.history      = []     # undo stack
        self.answer       = {}
        self.candidates   = defaultdict(list)
        self.cageID       = {}     # map cell to its cage
        self.future       = []     # redo stack
        self.parent       = parent

        self.makeCages(codeString)

        for x in range(dim):
            for y in range(dim):
                self.answer[x,y] = 0  #impossible value

        self.parent.control.setTime(0)            
                 
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
            op = operation['asmd'.index(clue[0])]
            answer = int(clue[1:])
            self.cages[id] = Cage(op, answer, cells)
        self.colorCages()

    def colorCages(self):
        '''
        Attempt to color the graph with 4 colors, using
        algorithm HybridEA from "A Guide to Graph Colouring" by 
        R.M.R. Lewis.  In the unlikely event that the resulting
        coloring uses more than 6 colors, fall back on color6
        '''
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

        if self.hybrid(adj):
            pass
        else:
            color6(adj)

    def hybrid(self, nbrs):
        # HybridEA
        ids = sorted(nbrs.keys())
        indices = {id :ids.index(id)+1 for id in ids}
        graph = {indices[v]:[indices[v] for v in nbrs[v]] for v in nbrs}
            
        vertices = len(graph)
        edges = sum(len(val) for val in graph.values())//2
        with open('dimacs.txt', 'w') as fout:
            fout.write(f'p edge {vertices} {edges}\n')
            for vertex in graph:
                for nbr in (n for n in graph[vertex] if n > vertex):
                    fout.write(f'e {vertex} {nbr}\n')
        run(['./HybridEA', '-T', '4', 'dimacs.txt'], capture_output=True)       
        coloring  = list(map(int, open('solution.txt').readlines()))[1:]


        # remove some of the artifacts

        os.remove('ceffort.txt')
        os.remove('teffort.txt')
        os.remove('dimacs.txt')
        os.remove('solution.txt')

        if max(coloring) > 5:
            return False
        for id, color in zip(ids, coloring):
            self.cages[id].color = color
        return True
        
    def enterAnswer(self, focus, value):
        
        # User enters an answer in a cell.

        # If the answer conflicts with a value already entered in another cell, 
        # or this answer completes a cage, and the arithmetic is wrong,
        # raise AnswerError.
        
        # If the user is entering (or changing) an answer, compute all resulting
        # inferences, enter them in the history, and return a list of all cells
        # whose values change (whether answers or candidates.)
        
        # If the user is simply reentering the same answer in a cell, do nothing
        # and return an empty list of updates.
        
        history     = self.history
        dim, answer = self.dim, self.answer
        
        if answer[focus] == value:
            return []
        
        row = [x for x in range(dim) if answer[(x, focus[1])] == value]
        col = [y for y in range(dim) if answer[(focus[0], y)] == value]
        cells = [(x, focus[1]) for x in row] + [(focus[0], y) for y in col]
        
        if cells:
            raise AnswerError(cells)
        
        id = self.cageID[focus]
        cage = self.cages[id]
        
        if len([x for x in cage if x != focus and answer[x]]) == len(cage) - 1:
            if not(self.goodAnswer(cage, focus, value)):
                raise AnswerError(cage)
            
        candidates = self.candidates[focus][:]
        before = answer[focus], candidates
        after = value, candidates
        history.append(Journal(focus, before, after))
        answer[focus] = value
        update = self.annal(focus)
        self.future = []
        return update
    
    def annal(self, focus):
        return Update(focus, self.answer[focus], self.candidates[focus][:])
    
    def toggleCandidate(self, focus, value):
        # Ignore if answer already in focus cell.
        # Otherwise, toggle the candidate value on or off.
                
        # Enter transaction in history and return update record
        
        history, answer, candidates = \
               self.history, self.answer, self.candidates
        
        if answer[focus]:                         # answer present
            return []
        
        ann = self.annal(focus)
        before = (ann.answer, ann.candidates)                   
        
        if value in candidates[focus]:            # toggle value off    
            candidates[focus].remove(value)                                     
        else:                                     # toggle value on 
            candidates[focus].append(value)
        after = (ann.answer, candidates[focus][:])  
        history.append(Journal(focus, before, after))
        self.future = []
        return self.annal(focus)
    
    def getAllEntries(self):
        # Return a list of updates for all cell that have a value (answer or candidate).
        # Used for redrawing the board
        
        dim = self.dim
        answer, candidates = self.answer, self.candidates
        updates = []
        for j in range(dim):
            for k in range(dim):
                if answer[(j, k)] or candidates[(j, k)]:
                    updates.append(self.annal( (j, k) ))
        return updates        
    
    def undo(self):
        # pop a journal entry of the undo stack and undo it
        # push it to the redo stack
        # return the update to post on the view
        
        answer, candidates, history = self.answer, self.candidates, self.history
        try:
            journal = history.pop()
        except IndexError:                    # user tried one too many undos
            return None
    
        coords             = journal.coords
        answer[coords]     = journal.b_ans
        candidates[coords] = journal.b_cand[:]
        self.future.append(journal)           # redo stack 
 
        return self.annal(coords)

    def redo(self):
        # pop a journal entry of the redo stack and redo it
        # push it to the undo stack
        # return the update to post on the view
        
        answer, candidates, future = self.answer, self.candidates, self.future
        try:
            journal = future.pop()
        except IndexError:                    # user tried one too many redos
            return None
    
        coords             = journal.coords
        answer[coords]     = journal.a_ans
        candidates[coords] = journal.a_cand[:]
        self.history.append(journal)           # redo stack 
 
        return self.annal(coords)
    
    def clearCell(self, focus):
        # If there is an answer in the current cell clear it.
        # If there is no answer, clear the candidate list.
        # Return a list of updates
        
        answer, candidates, history = self.answer, self.candidates, self.history
        if not answer[focus] and not candidates[focus]:
            return []                                # nothing to clear
        
        ann = self.annal(focus)   
        before = (ann.answer, ann.candidates)     
        if answer[focus]:
            answer[focus] = 0
        else:
            candidates[focus] = []
        ann = self.annal(focus)
        after = (ann.answer, ann.candidates)
        history.append(Journal(focus, before, after)) 
        self.future = []
        return ann
            
    def isCompleted(self):
        # Has user entered answer in each cell?
        
        return len([x for x in list(self.answer.values()) if x]) == self.dim ** 2

    def restart(self):
        # Clear all user-entered data
        # User wants to start over
        
        dim = self.dim
        for i in range(dim):
            for j in range(dim):
                self.candidates[(i,j)] = []
                self.answer[(i,j)] = 0
        self.history = []        
        
    def goodAnswer(self, cage, focus, value):
        # Precondition: Evey cell in cage, except focus, has an filled in
        # Return true iff filling value into focus makes the
        # arithmetic work out
        
        result = None
        operands = [self.answer[x] for x in cage if x != focus]
        operands += [value]
        if cage.op == ADD:
            result = sum(operands) == cage.value
        elif cage.op == SUB:
            result = max(operands) - min(operands) == cage.value
        elif cage.op == MUL:
            product = 1
            for x in operands:
                product *= x
            result  = product == cage.value
        elif cage.op == DIV:
            result = max(operands) == min(operands) * cage.value
        return result
        