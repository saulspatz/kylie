from email.policy import default
import random
from collections import defaultdict

from matplotlib import colors
'''
Greedy coloring;, smallest last

Graph is represented as an adjacency dict
Each vertex appears as a key.  The value is a list of
vertices adjacent to the key 
'''

def SL(graph):
    answer = []
    h = list(graph.keys())
    degree = {}
    invDegree = defaultdict(list)
    for k, v in graph.items():
        deg = len(v)
        degree[k] = deg
        invDegree[deg].append(k)
    n = len(graph)
    for _ in range(n):
        deg = min(d for d in invDegree if invDegree[d])
        vertex = random.choice(invDegree[deg])
        answer.append(vertex)
        h.remove(vertex)
        invDegree[deg].remove(vertex)
        for nbr in graph[vertex]:
            if nbr not in h:
                continue
            d = degree[nbr]
            invDegree[d].remove(nbr)
            invDegree[d-1].append(nbr)
            degree[nbr] = d-1
    return answer

def greedyColor(graph, maxColors, maxTries):
    possible = set(range(1, len(graph)+1))
    for k in range(maxTries):
        order = SL(graph)
        color= {}
        for vertex in order:
            color[vertex] = 0
        for vertex in order:
            nbrColors = {color[nbr] for nbr in graph[vertex]}
            c = min(possible-nbrColors)
            if c > maxColors:
                break
            color[vertex] = c
        else:
            return color
    print('fail')
    return None





    
