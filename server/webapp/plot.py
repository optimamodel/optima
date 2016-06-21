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


def reformat(figure):
    figure.set_size_inches(6, 3)
    n_label = 0
    for axes in figure.axes:
        legend = axes.get_legend()
        if legend is not None:
            labels = legend.get_texts()
            n_label = len(labels)

            # Put a legend to the right of the current axis
            box = axes.get_position()
            axes.set_position(
                [box.x0, box.y0+box.height*0.1, box.width * 0.75, box.height*0.9])
            legend._loc = 2
            legend.set_bbox_to_anchor((1, 1.02))

    return n_label


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

    graphs = op.plotting.makeplots(result, toplot=which, figsize=(4, 3))

    graph_selectors = []
    mpld3_graphs = []

    for graph_key in graphs:
        # Add necessary plugins here
        graph = graphs[graph_key]

        plugin = mpld3.plugins.MousePosition(fontsize=14, fmt='.4r')
        mpld3.plugins.connect(graph, plugin)

        n_label = reformat(graph)
        mpld3_dict = mpld3.fig_to_dict(graphs[graph_key])
        mpld3_dict['nLengendLabel'] = n_label

        # get rid of NaN
        mpld3_dict = normalize_obj(mpld3_dict)

        graph_selectors.append(extract_graph_selector(graph_key))
        mpld3_graphs.append(mpld3_dict)

    return {
        'graphs': {
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors
        }
    }