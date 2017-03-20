import re

import mpld3

from matplotlib.transforms import Bbox
from numpy import array

import optima as op

from .parse import normalize_obj


def extract_graph_selector(graph_key):
    s = repr(str(graph_key))
    base = "".join(re.findall("[a-zA-Z]+", s.split(",")[0]))
    if "'t'" in s:
        suffix = "-tot"
    elif "'p'" in s:
        suffix = "-pop"
    elif "'s'" in s:
        suffix = "-sta"
    else:
        suffix = ""
    return base + suffix


def convert_to_mpld3(figure):
    plugin = mpld3.plugins.MousePosition(fontsize=8, fmt='.4r')
    mpld3.plugins.connect(figure, plugin)

    figure.set_size_inches(5.5, 2)

    if len(figure.axes) == 1:
        ax = figure.axes[0]
        legend = ax.get_legend()
        if legend is not None:
            # Put a legend to the right of the current axis
            legend._loc = 2
            legend.set_bbox_to_anchor((1, 1.1))
            ax.set_position(Bbox(array([[0.19, 0.1], [0.65, 0.85]])))
        else:
            ax.set_position(Bbox(array([[0.19, 0.1], [0.85, 0.85]])))

    mpld3_dict = mpld3.fig_to_dict(figure)
    graph_dict = normalize_obj(mpld3_dict)
    
    # WARNING, kludgy -- remove word None that appears
    texts = graph_dict['axes'][0]['texts']
    for i in reversed(range(len(texts))):
        if texts[i]['text'] == 'None':
            del texts[i]
    
    return graph_dict


def convert_to_selectors(graph_selectors):
    keys = graph_selectors['keys']
    names = graph_selectors['names']
    defaults = graph_selectors['defaults']
    selectors = [
        {'key': key, 'name': name, 'checked': checked}
         for (key, name, checked) in zip(keys, names, defaults)]
    return selectors


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
    print ">> make_mpld3_graph_dict input which:", which

    if which is None:
        advanced = False
        if hasattr(result, 'which'):
            which = result.which
            if which is None:
                which = {}
            print ">> make_mpld3_graph_dict has cache:", which
            if 'advanced' in which:
                advanced = True
                which.remove("advanced")
        else:
            which = ["default"]
    else:
        advanced = False
        if 'advanced' in which:
            advanced = True
            which.remove('advanced')

    print ">> make_mpld3_graph_dict advanced:", advanced

    graph_selectors = op.getplotselections(result, advanced=advanced) # BOSCO MODIFY
    if advanced:
        normal_graph_selectors = op.getplotselections(result)
        n = len(normal_graph_selectors['keys'])
        normal_default_keys = []
        for i in range(n):
            if normal_graph_selectors["defaults"][i]:
                normal_default_keys.append(normal_graph_selectors["keys"][i])
        normal_default_keys = tuple(normal_default_keys)
        # rough and dirty defaults for missing defaults in advanced
        n = len(graph_selectors['keys'])
        for i in range(n):
            key = graph_selectors['keys'][i]
            if key.startswith(normal_default_keys) and ('total' in key or 'stacked' in key):
                graph_selectors['defaults'][i] = True
    selectors = convert_to_selectors(graph_selectors)

    default_which = []
    for i in range(len(graph_selectors['defaults'])):
        if graph_selectors['defaults'][i]:
            default_which.append(graph_selectors['keys'][i])

    if len(which) == 0 or 'default' in which:
        which = default_which
    else:
        which = [w for w in which if w in graph_selectors["keys"]]
        for selector in selectors:
            selector['checked'] = selector['key'] in which

    print ">> make_mpld3_graph_dict which:", which

    graphs = op.makeplots(result, toplot=which, figsize=(4, 3), die=False)
    op.reanimateplots(graphs)

    graph_selectors = []
    mpld3_graphs = []
    for graph_key in graphs:
        graph_selectors.append(extract_graph_selector(graph_key))
        graph_dict = convert_to_mpld3(graphs[graph_key])
        if graph_key == "budget":
            graph = graphs[graph_key]
            ylabels = [l.get_text() for l in graph.axes[0].get_yticklabels()]
            graph_dict['ylabels'] = ylabels
        mpld3_graphs.append(graph_dict)

    return {
        'graphs': {
            "advanced": advanced,
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors,
            'resultId': str(result.uid),
        }
    }
