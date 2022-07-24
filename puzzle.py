from collections import defaultdict, namedtuple
from itertools import combinations
import re
import os
from random import choice, shuffle, randint
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
                    # horizontal edge
                    col = cursor//(dim-1) 
                    row = cursor%(dim-1)   
                    p0 =  row, col
                    p1 =  row+1, col
                else:
                    # vertical edge
                    row = cursor//(dim-1)-dim 
                    col = cursor%(dim-1) + 1
                    p0 = row, col-1
                    p1 = row, col
                union = blocks[p0] | blocks[p1]
                for cell in union:
                    blocks[cell] = union
                cursor += 1
            cursor += 1
        
        # I have the cell indices as (row, col), whereas Tatham uses
        # (col, row).  The transpose function is used to make an 
        # exact replica, rather than the transpose.
        
        transpose = lambda x: (x[1], x[0])
        cages = {}
        cages = {b:blocks[b] for b in blocks if b== min(blocks[b], key=transpose)}
        pattern =re.compile(r'[adms][0-9]+')
        clues = pattern.findall(operCode)
        try:
            assert len(cages) == len(clues)
        except:
            print(codeString)
            for item in cages.items():
                print(item)
        for id, clue  in zip(sorted(cages, key = transpose), clues):
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
        the iterated greedy algorithm 
        from "A Guide to Graph Colouring" by 
        R.M.R. Lewis.  In the unlikely event that the resulting
        coloring uses more than 6 colors, fall back on color6
        '''
        cages = self.cages
        def color6(graph): 
            if len(graph)== 1:
                id = list(graph.keys())[0]
                cages[id].color = 0
                return
            for id in graph:   # There must be a vertex of degree <= 5
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

        if not self.iteratedGreedy(adj):
            color6(adj)

    def iteratedGreedy(self, adj):
        coloring, tries = GraphColorer(adj).iteratedGreedy(50, 4)
        colors = max(coloring.values())+1
        with open('results.log', 'a') as fout:
            fout.write(f"{colors} colors {tries} iteration{'s' if tries > 1 else ''}\n")
        if colors > 6:
            return False
        for id, color in coloring.items():
            self.cages[id].color = color
        return True


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
        
class GraphColorer:
    def __init__(self, adj: dict[set]) -> None:       
        V = self.V = list(adj.keys())
        self.nbrs = adj
        self.n = len(self.V)
        self.degree = {i: len(self.nbrs[i]) for i in V}
        self.color = {i: 0 for i in V}
        self.dsat = {i: 0 for i in V}
        self.colorClass = defaultdict(set)

    def choose(self, X) -> None:
        # Return vertex with greatest degree of saturation
        # Break ties by highest degree
        # Break any remaining tie randomly
  
        deg = self.degree
        sat = self.dsat
        s, d = max((sat[v],deg[v]) for v in X)
        candidates = [v for v in X if sat[v]==s and deg[v]==d]
        return choice(candidates)

    def DSatur(self) -> None:
        X = self.V.copy()  # uncolored vertices
        S = self.colorClass
        nbrs = self.nbrs
        nbrColors = defaultdict(set)
        while X:
            v = self.choose(X)
            if not S:
                S[0].add(v)
                X.remove(v)
                continue
            for j in range(len(S)):
                if not S[j] & nbrs[v]:
                    S[j].add(v)
                    break
            else: # loop else
                j += 1
                S[j].add(v)
            for u in nbrs[v]:
                nbrColors[u].add(j)
                self.dsat[u] = len(nbrColors[u])
            X.remove(v)

    def greedy(self) -> None:
        colorClass = self.colorClass = defaultdict(set)
        V = self.V
        nbrs = self.nbrs
        colorClass[0].add(V[0])
        for v in V[1:]:
            for c in colorClass:
                if not (nbrs[v] & colorClass[c]):
                    colorClass[c].add(v)
                    break
            else:   # loop else
                colorClass[c+1].add(v)

    def flatten(self, X:list[set]) -> list:
        return [x for s in X for x in s]

    def largestFirst(self) -> None:
        # Reorder the vertices in order of the color classes
        # in decreasing order of size

        #print('largestFirst')
        #old = self.V
        c = sorted(self.colorClass.values(), key= lambda x:len(x), reverse=True)
        self.V = self.flatten(c)
        # if old == self.V:
        #     print('no change')
        #self.printV()

    def reverse(self) -> None:
        # Reorder the vertices in the reverse of the color classes
       
        # print('reverse')
        # old = self.V
        classes = self.colorClass
        c = [classes[i] for i in range(len(classes))]
        self.V = self.flatten(c)
        # if old == self.V:
        #     print('no change')
        #self.printV()

    def randomize(self) -> None:
        # Reorder the vertices by shuffling the color classes
       
        # print('randomize')
        # old = self.V
        c = list(self.colorClass.values())
        shuffle(c)
        self.V = self.flatten(c)
        # if old == self.V:
        #     print('no change')
        #self.printV()

    def printV(self):
        for v in self.V:
            print(self.V, end = ' ')
        print()

    def iteratedGreedy(self, limit: int, goal:int = 0) -> tuple[dict, int]:
        # Iterated greedy coloring
        # limit is the maximum number of colorings to try
        # goal is a target for the number of colors; if
        # this goal is achieved, the coloring stops early.
        # The default goal is 0, so there is no target

        self.DSatur()    # color initially with DSatur algorithm
        tries = 1
        if len(self.colorClass) <= goal:
            # Color the graph
            colors = self.colorClass
            self.color = {v:c for c in colors for v in colors[c]}
            return self.color, 1
        while tries < limit:
            r = randint(1,13)

            # Reorder the vertices according to largesrt first, reversal,
            # or random shuffling randomly, with proportin 5:5:3, and
            # then use the greedy algorithm
              
            if r <= 5:
                self.largestFirst()
            elif r <= 10:
                self.reverse()
            else:
                self.randomize()
            self.greedy()
            tries += 1
            if len(self.colorClass) <= goal:
                break
        colors = self.colorClass

        # Color the graph
        self.color = {v:c for c in colors for v in colors[c]}

        return self.color, tries
