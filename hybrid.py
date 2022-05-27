from kenken import KenKen
from puzzle import Puzzle
import tkinter as tk
from subprocess import run

root = tk.Tk()
ken = KenKen(root)

for _ in range(1000):
    ken.newPuzzle(9)
    nbrs = ken.puzzle.graph
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
    path = '/home/saul/Projects/GraphColouring/HybridEA/HybridEA'
    run([path, '-T', '4', 'dimacs.txt'], capture_output=True)
