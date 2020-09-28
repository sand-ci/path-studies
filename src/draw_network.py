import numpy as np
import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path
from cycler import cycler
from itertools import combinations
import src.make_network as mn

PROJECT_ROOT = Path.cwd()


def draw_network(G, edge_label='count'):
#     if 'version' not in G.graph:
#         G.graph['version'] = '0'
    
    file_name = G.graph['name'] + '.png'
    file_path = str(PROJECT_ROOT / 'figures' / file_name)
    
    fig, ax = plt.subplots(figsize=(12, 12))
    plt.title('Network with the ' + str(len(G.edges)) + ' most central edges')
    
    nx.draw(G, nx.spring_layout(G), edgelist=G.edges, node_size=10)
#     nx.draw_networkx_edge_labels(G, nx.spring_layout(G), edgelist=G.edges, edge_labels=nx.get_edge_attributes(G, edge_label))
    
    plt.savefig(file_path, bbox_inches='tight')
    plt.close(fig)


def draw_networks(G, edge_lists, node_lists):
    pos = nx.spring_layout(G)
    for i in range(len(edge_lists)):
        file_name = G.graph['name'] + '_' + str(len(edge_lists[i])).zfill(5) + '.png'
        file_path = str(PROJECT_ROOT / 'figures' / file_name)
        
        fig, ax = plt.subplots(figsize=(12, 12))
        plt.title('Network with the ' + str(len(edge_lists[i])) + ' most central edges')
        
        nx.draw(G, pos, nodelist=node_lists[i], edgelist=edge_lists[i], node_size=10)
        plt.savefig(file_path, bbox_inches='tight')
        plt.close(fig)