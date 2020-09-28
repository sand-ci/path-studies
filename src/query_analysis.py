import src.es_queries as esq
import datetime as dt
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path.cwd()

bad_pairs = {}
ps_adj = {}       # Adjacency list for ps pairs (i.e., for any given source, a list of destinations that are connected)
ps_pairs = []     # List of unique ps pairs
routes = {}
route_change = {}
edge_counts = {}


def reset_vars():
    global bad_pairs
    global ps_adj
    global ps_pairs
    global routes
    global route_change
    global core_edges
    bad_pairs = {}
    ps_adj = {}       # Adjacency list for ps pairs (i.e., for any given source, a list of destinations that are connected)
    ps_pairs = []     # List of unique ps pairs
    routes = {}
    route_change = {}
    edge_counts = {}


def extract_srcdest(srcdest):
    """ Extract src/dest ips from _source.
    
    Args:
        srcdest (dict): Entry from trace_derived_v2
    
    Returns:
        str, str: ip addresses for source and destination        
    """
    return srcdest['src'], srcdest['dest']


def is_bad_pair(src=None, dest=None, srcdest=None):
    """ Check whether a src/dest pair has been added to the bad_pairs dictionary yet.
    
    Args:
        src (str): Source IP address
        dest (str): Destination IP address
        srcdest (dict): Entry from trace_derived_v2
    
    Returns:
        bool: Whether given pair is in bad_pairs
    """
    global bad_pairs
    if srcdest:
        src, dest = extract_srcdest(srcdest)
    return (src, dest) in bad_pairs


def is_ps_pair(src=None, dest=None, srcdest=None):
    """ Check whether a src/dest pair is in ps_pair.
    
    Args:
        src (str): Source IP address
        dest (str): Destination IP address
        srcdest (dict): Entry from trace_derived_v2
    
    Returns:
        bool: Whether given pair is in ps_pairs
    """
    global ps_pairs
    if srcdest:
        src, dest = extract_srcdest(srcdest)
    return (src, dest) in ps_pairs


def add_bad_pair(src=None, dest=None, srcdest=None, problem=None):
    """ Add a pair of nodes to bad_pair along with the problem for which they are to be omitted.
    
    Args:
        src (str): Source IP address
        dest (str): Destination IP address
        srcdest (dict): Entry from trace_derived_v2
        problem (str): Reason why pair should be omitted
    """
    global bad_pairs
    global ps_pairs
    global ps_adj
    global routes
    
    if srcdest:
        src, dest = extract_srcdest(srcdest)

    if src in ps_adj:
        if dest in ps_adj[src]:
            ps_adj[src].remove(dest)
    if (src, dest) in ps_pairs:
        ps_pairs.remove((src, dest))
    if (src, dest) in routes:
        routes.pop((src, dest))
        
    if is_bad_pair(src=src, dest=dest):
        bad_pairs[(src, dest)].append(problem)
    else:
        bad_pairs[(src, dest)] = [problem]


def make_ps_pairs(td_scan):
    """ Iterate through generator to evaluate each pair of perfsonar nodes, flagging ones to be omitted
    
    Args:
        td_scan (generator): Generator for iterating through trace_derived_v2
    
    Returns:
        list, dict: List of valid ps_pairs and adjacency list (dictionary) representation of pairs.
    """
    duplicates = 0    # Number of pairs that were already added to ps_pairs
    global ps_adj
    global ps_pairs

    for srcdest in td_scan:
        # Omit pairs with less than 1 hop (impossible!)
        if srcdest['n_hops']['avg'] < 1:
            problem = 'hops'
            add_bad_pair(srcdest=srcdest, problem=problem)

        # Omit pairs that have fewer than 1000 records
        if srcdest['n_hops']['value_count'] < 1000:
            problem = 'count'
            add_bad_pair(srcdest=srcdest, problem=problem)

        if not is_bad_pair(srcdest=srcdest):
            if srcdest['src'] in ps_adj: 
                if srcdest['dest'] not in ps_adj[srcdest['src']]:
                    ps_adj[srcdest['src']].append(srcdest['dest'])
                    ps_pairs.append((srcdest['src'], srcdest['dest']))
                else:
                    duplicates += 1
            else:
                ps_adj[srcdest['src']] = [srcdest['dest']]
                ps_pairs.append((srcdest['src'], srcdest['dest']))
    
    before = (len(ps_pairs), len(ps_adj))
    after = (0, 0)
    problem = 'nonsymmetry'

    # Remove ps pairs that do not have a two-way connection; repeats until stable
    while before != after:
        before = (len(ps_pairs), len(ps_adj))
        for src in list(ps_adj.keys()):
            for dest in ps_adj[src]:
                if dest not in ps_adj:
                    add_bad_pair(src=src, dest=dest, problem=problem)
                elif src not in ps_adj[dest]:
                    add_bad_pair(src=src, dest=dest, problem=problem)
            if not ps_adj[src]:
                ps_adj.pop(src)
        after = (len(ps_pairs), len(ps_adj))
    print("Successfully identified", len(ps_pairs), "perfSONAR pairs.")
    

def get_ps_pairs():
    global ps_pairs
    return ps_pairs


def stable_routes(ps_trace):
    global routes
    for trace in ps_trace:
#         trace = trace['_source']
#         if not trace['src_production'] or not trace['dest_production']:
#             continue
        try:
            src = trace['src']
            dest = trace['dest']
            sha = trace['route-sha1']
            hops = trace['hops']
#             max_rtt = trace['max_rtt']
#             looping = trace['looping']
        except KeyError:
            continue

        if is_ps_pair(src=src, dest=dest):
            if looping:
                if (src, dest) in routes:
                    add_bad_pair(src=src, dest=dest, problem='looping')
                    
            elif (src, dest) in routes:
                if sha == routes[(src, dest)]['sha']:
                    if max_rtt > routes[(src, dest)]['max_rtt']:
                        routes[(src, dest)]['max_rtt'] = max_rtt
                    routes[(src, dest)]['records'] = routes[(src, dest)]['records'] + 1
                else:
                    add_bad_pair(src=src, dest=dest, problem='unstable')
            else:
                routes[(src, dest)] = {'sha': sha, 'hops': hops, 'max_rtt': max_rtt, 'records': 1}
                

def get_stable_routes():
    global routes
    return routes


def route_changes(ps_trace, file_name='route_changes.pa'):
    global route_change
    for trace in ps_trace:
        try:
            src = trace['src']
            dest = trace['dest']
            sha = trace['route-sha1']
            time = trace['timestamp']
        except KeyError:
            continue

#         if is_ps_pair(src=src, dest=dest):
        if (src, dest) in route_change:
            if sha != route_change[(src, dest)]['sha']:
                route_change[(src, dest)]['sha'] = sha
                route_change[(src, dest)]['change'].append(time)
        else:
            route_change[(src, dest)] = {'sha': sha, 'change': [time]}
    rc_temp = []
    for key in route_change:
        rc_temp.append({'src': key[0], 'dest': key[1], 'sha': route_change[key]['sha'], 'changetimes': route_change[key]['change']})
    df = pd.DataFrame(rc_temp)
    df.to_parquet(str(PROJECT_ROOT / 'data' / file_name), engine='pyarrow')
    print("Successfully identified", len(route_change), "routes that had activity.")

                
def get_route_changes():
    global route_change
    return route_change


def load_route_changes(file_name='route_changes.pa'):
    df = pd.read_parquet(str(PROJECT_ROOT / 'data' / file_name))


def route_life(time):
    global route_change
    avg_route_life = {}
    for route in route_change:
#         total_time = 0
#         for i in range(len(route_change[route]['change']) - 1):
#             total_time += route_change[route]['change'][i + 1] - route_change[route]['change'][i]
        avg_route_life[route] = time / len(route_change[route]['change'])
    return avg_route_life


def count_edges(ps_trace):
    global edge_counts
    for trace in ps_trace:
#         trace = trace['_source']
        try:
            hops = trace['hops']
        except KeyError:
            continue
            
        for i in range(len(hops) - 1):
            s = hops[i]
            d = hops[i+1]
            if (s, d) in edge_counts:
                edge_counts[(s, d)] = edge_counts[(s, d)] + 1
            elif (d, s) in core_edges:
                edge_counts[(d, s)] = edge_counts[(d, s)] + 1
            else:
                edge_counts[(s, d)] = 1

                
def get_edge_counts():
    global edge_counts
    return edge_counts


def save_data(scan_gen, file_name):
    data = []
    records = 0
    for trace in scan_gen:
        data.append(trace)
        records += 1
        if not records % 100000:
            print(records)
    print(records)
    df = pd.DataFrame(data)
    df.to_parquet(str(PROJECT_ROOT / 'data' / file_name), engine='pyarrow')

    
def load_dataframe(file_name):
    return pd.read_parquet(str(PROJECT_ROOT / 'data' / file_name), engine='pyarrow')