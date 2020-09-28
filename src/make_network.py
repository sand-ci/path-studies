from datetime import datetime
from pathlib import Path
import networkx as nx
import numpy as np
import pandas as pd
from itertools import combinations
from copy import deepcopy
import re

PROJECT_ROOT = Path.cwd()


def load_network(name, version):
    if not version:
        graph_file = name + '.gz'
        graph_path = PROJECT_ROOT / 'data' / graph_file
    else:
        graph_file = name + '_v' + str(version) + '.gz'
        graph_path = PROJECT_ROOT / 'data' / graph_file

    G = nx.read_gml(graph_path)
    
    return G


def save_network(G, version=0):
    if version:
        G.graph['version'] = str(version)
    
    if 'version' not in  G.graph:
        G.graph['version'] = '0'
        graph_file = G.graph['name'] + '.gz'
        graph_path = PROJECT_ROOT / 'data' / graph_file
    elif G.graph['version'].isnumeric():
        G.graph['version'] = str(int(G.graph['version']) + 1)
        graph_file = G.graph['name'] + '_v' + G.graph['version'] + '.gz'
        graph_path = PROJECT_ROOT / 'data' / graph_file
    else:
        graph_file = G.graph['name'] + '_v' + G.graph['version'] + '.gz'
        graph_path = PROJECT_ROOT / 'data' / graph_file
    
    nx.write_gml(G, graph_path)
    return G


def make_network(graph_name="Network", edges=[]):
    G = nx.Graph(name=graph_name + "_" + str(len(edges)).zfill(5))# str(datetime.timestamp(datetime.now())))
    
    for edge in edges:
        G.add_edge(edge[0][0], edge[0][1], count=edge[1])
    
    G = save_network(G)
    return G

