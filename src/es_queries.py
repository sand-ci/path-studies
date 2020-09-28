from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan, bulk


def es_login(username=None, password=None, filename="credentials.key"):
    """ Create and log into an ElasticSearch instance.
    
    Args:
        username (str)
        password (str)
        filename (str): relative path and name of credentials file.
    
    Returns:
        Elasticsearch: An logged-in instance of ElasticSearch.
    """
    
    if not username or not password:
        try:
            with open(filename) as f:
                username = f.readline().strip()
                password = f.readline().strip()
        except:
            print("Valid credentials were not found.")
            return
    
    credentials = (username, password)
    es = Elasticsearch([{'host': 'atlas-kibana.mwt2.org', 'port': 9200, 'scheme': 'https'}], timeout=240, http_auth=credentials)

    if es.ping():
        print("Connection Successful")
    else:
        print("Connection Unsuccessful")
    
    return es


def list_to_eslist(pylist):
    """ Converts python list of strings to a string of that list that can be used in ES.
    
    Args:
        pylist (list): Each element is a str.
    
    Returns:
        str: A representation of the list with each item in double quotes.
    """
    eslist = '[ '
    
    for item in pylist[:-1]:
        eslist += '"' + item + '", '
    
    eslist += '"' + pylist[-1] + '" ]'
    
    return eslist


def get_unique_pairs(es):
    """ Query to directly get matching pairs of PS nodes.
    
    Args:
        es (Elasticsearch object): Current elasticsearch connection object.
    
    Returns:
        dict: An double aggregation of sources and corresponding destinations.
        
    """
    query = {
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "n_hops.avg": {
                                "gt": 1
                            }
                        }
                    },
                    {
                        "range": {
                            "n_hops.value_count": {
                                "gt": 1000
                            }
                        }
                    }
                ]
            }
        },
        "aggs": {
            "sources": {
                "terms": {
                    "field": "src",
                    "size": 60
                },
                "aggs": {
                    "destinations": {
                        "terms": {
                            "field": "dest", 
                            "size": 59
                        }
                    }
                }
            }
        }
    }
    
    try:
        return es.search(index="trace_derived_v2", body=query)
    except Exception as e:
        print(e)


def trace_derived_scan(es):
    """ Create a generator object for trace_derived_v2
    
    Args:
        es (Elasticsearch object): Current elasticsearch connection object.
    
    Returns:
        generator: For iterating through trace_derived_v2.
        
    """
    try:
        return scan_gen(scan(es, index="trace_derived_v2", _source=["src", "dest", "n_hops"], filter_path=['_scroll_id', '_shards', 'hits.hits._source'])) #, query=query)
    except Exception as e:
        print(e)


def ps_trace_scan(es, start, end, include=["src", "dest", "timestamp", "hops", "route-sha1"]):
    """ Create a generator object for ps_trace with a given start, end date and (optional) set of ps nodes.
    
    Args:
        es (Elasticsearch object): Current elasticsearch connection object.
        start (str): Start of time interval to pull (formatted "%Y-%m-%dT%H:%M:%S.000Z").
        end (str): End of time interval to pull (formatted "%Y-%m-%dT%H:%M:%S.000Z").
    
    Returns:
        generator: For iterating through results in ps_trace.
        
    """
    query = {
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            "timestamp": {
                                "gte": start,
                                "lte": end,
                                "format": "strict_date_optional_time"
                            }
                        }
                    },
                    {
                        "term": {
                            "looping": False
                        }
                    },
                    {
                        "term": {
                            "src_production": True
                        }
                    },
                    {
                        "term": {
                            "dest_production": True
                        }
                    }
                ]
            }
        }
    }
    
    try:
        return scan_gen(scan(es, index="ps_trace", query=query, _source=include, filter_path=['_scroll_id', '_shards', 'hits.hits._source']))
    except Exception as e:
        print(e)
        
        
def scan_gen(scan):
    while True:
        try:
            yield next(scan)['_source']
        except:
            break