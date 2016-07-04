import re

import mpld3

from matplotlib.transforms import Bbox
from numpy import array
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


def convert_to_mpld3(figure):
    plugin = mpld3.plugins.MousePosition(fontsize=0, fmt='.4r')
    mpld3.plugins.connect(figure, plugin)

<<<<<<< HEAD
    if len(figure.axes) == 1:
        for ax in figure.axes:
            legend = ax.get_legend()
            if legend is not None:
                # Put a legend to the right of the current axis
                legend._loc = 2
                legend.set_bbox_to_anchor((1, 1.1))
                ax.set_position(Bbox(array([[0.19, 0.55], [0.7, 0.92]])))
            else:
                ax.set_position(Bbox(array([[0.19, 0.55], [0.95, 0.92]])))

        for ax in figure.axes:
            ax.yaxis.label.set_size(14)
            ax.xaxis.label.set_size(14)
            ax.title.set_size(14)

            ticklabels = ax.get_xticklabels() + ax.get_yticklabels()
            for ticklabel in ticklabels:
                ticklabel.set_size(10)
            legend = ax.get_legend()
            if legend is not None:
                texts = legend.get_texts()
                for text in texts:
                    text.set_size(10)
=======
    is_stack_plot = False
    for ax in figure.axes:
        legend = ax.get_legend()
        labels = legend.get_texts()
        if len(labels) == 1:
            label = labels[0]
            if label.get_text() == "Model":
                legend.remove()
                legend = None
        if legend is not None:
            # Put a legend to the right of the current axis
            legend._loc = 2
            legend.set_bbox_to_anchor((1, 1.1))
            ax.set_position(Bbox(array([[0.19, 0.55], [0.7, 0.92]])))
            is_stack_plot = True
        else:
            ax.set_position(Bbox(array([[0.19, 0.2], [0.95, 0.92]])))

    if is_stack_plot:
        figure.set_size_inches(5, 4)
    else:
        figure.set_size_inches(5, 2.5)
>>>>>>> 14c58eb7e4077486735b40bccca233e0cb5f20ec



    mpld3_dict = mpld3.fig_to_dict(figure)
    return normalize_obj(mpld3_dict)


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
        graph_selectors.append(extract_graph_selector(graph_key))
        mpld3_graphs.append(convert_to_mpld3(graphs[graph_key]))

    return {
        'graphs': {
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors,
            'resultId': str(result.uid),
        }
    }