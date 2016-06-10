import re

import mpld3

import optima as op
from server.webapp.utils import normalize_obj


def extract_graph_selector(graph_key):
    s = repr(str(graph_key))
    base = "".join(re.findall("[a-zA-Z]+", s.split(",")[0]))
    if "'t'" in s:
        suffix = "-tot"
    elif "'p'" in s:
        suffix = "-per"
    elif "'s'" in s:
        suffix = "-sta"
    else:
        suffix = ""
    return base + suffix


def make_mpld3_graph_dict(result, which=None):
    """
    Converts an Optima sim Result into a dictionary containing
    mpld3 graph dictionaries and associated keys for display,
    which can be exported as JSON.

    Args:
        result: the Optima simulation Result object
        which: a list of keys to determine which plots to generate

    Returns:
        A dictionary of the form:
            { "graphs":
                "mpld3_graphs": [<mpld3 graph dictioanry>...],
                "graph_selectors": ["key of a selector",...],
                "selectors": [<selector dictionary>]
            }
            - mpld3_graphs is the same length as graph_selectors
            - selectors are shown on screen and graph_selectors refer to selectors
            - selector: {
                "key": "unique name",
                "name": "Long description",
                "checked": boolean
              }
        }
    """

    graph_selectors = op.getplotselections(result)
    keys = graph_selectors['keys']
    names = graph_selectors['names']
    checks = graph_selectors['defaults']
    selectors = [
        {'key': key, 'name': name, 'checked': checked}
         for (key, name, checked) in zip(keys, names, checks)]

    if which is None:
        which = [s["key"] for s in selectors if s["checked"]]
    else:
        for selector in selectors:
            selector['checked'] = selector['key'] in which

    for selector in selectors:
        if not selector['checked']:
            selector['name'] = '(unloaded) ' + selector['name']

    print "> which: ", which
    print "> keys: ", keys
    print "> names: ", names
    print "> checks: ", checks
    # which = keys
    graphs = op.plotting.makeplots(result, toplot=which, figsize=(4, 3))

    graph_selectors = []
    mpld3_graphs = []
    print "> graph.type", type(graphs)
    print "> graph-keys: ", graphs.keys()
    for graph_key in graphs:
        # Add necessary plugins here
        mpld3.plugins.connect(
            graphs[graph_key],
            mpld3.plugins.MousePosition(fontsize=14, fmt='.4r'))

        mpld3_dict = mpld3.fig_to_dict(graphs[graph_key])

        # get rid of NaN
        mpld3_dict = normalize_obj(mpld3_dict)

        graph_selectors.append(extract_graph_selector(graph_key))
        mpld3_graphs.append(mpld3_dict)

    print "> graphs_selectors: ", graph_selectors
    return {
        'graphs': {
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors
        }
    }