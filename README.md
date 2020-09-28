Path Studies
==============================

Tools for extracting data from a network using Elasticsearch, analyzing that data and creating a representation of that network.

Project Organization
------------

    ├── LICENSE
    ├── README.md               <- The top-level README for developers using this project.
    │
    ├── requirements.txt        <- The requirements file for reproducing the analysis environment, 
    │                              e.g. generated with `pip freeze > requirements.txt`.
    ├── Main.ipynb              <- Notebook containing primary analysis.
    │
    ├── Test.ipynb              <- Home to code snippets that did not make it in Main or src files.
    │
    ├── data
    │
    ├── figures        	        <- Generated graphics and figures to be used in reporting.
    │
    └── src                     <- Source code for use in this project.
        ├── draw_network.py     <- Tools for visualizing a graph representation of the network.
        │
        ├── make_networks.py    <- Tools for creating a graph representation of the network.
        │
        ├── es_queries.py       <- Elasticsearch queries.
        │
        └── query_analysis.py   <- Tools for working with data pulled from Elasticsearch.
