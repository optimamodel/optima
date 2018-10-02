import re

import mpld3

from matplotlib.transforms import Bbox
from numpy import array

import optima as op

from .parse import normalize_obj

frontendfigsize = (5.5, 2)
frontendpositionnolegend = [[0.19, 0.12], [0.85, 0.85]]
frontendpositionlegend   = [[0.19, 0.12], [0.63, 0.85]]
frontendpositionmidway   = [[0.19, 0.12], [0.80, 0.85]]


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


def convert_to_mpld3(figure, zoom=None, graph_pos=None):
    plugin = mpld3.plugins.MousePosition(fontsize=8, fmt='.4r')
    mpld3.plugins.connect(figure, plugin)
    
    # Handle figure size
    if zoom is None: zoom = 0.8
    zoom = 1.8 - zoom
    figsize = (frontendfigsize[0]*zoom, frontendfigsize[1]*zoom)
    figure.set_size_inches(figsize)

    if len(figure.axes) == 1:
        ax = figure.axes[0]
        legend = ax.get_legend()
        if legend is not None:
            # Put a legend to the right of the current axis
            legend._loc = 2
            legend.set_bbox_to_anchor((1, 1.1))
            if graph_pos=='mid': ax.set_position(Bbox(array(frontendpositionmidway)))
            else:                ax.set_position(Bbox(array(frontendpositionlegend)))
        else:
            ax.set_position(Bbox(array(frontendpositionnolegend)))

    mpld3_dict = mpld3.fig_to_dict(figure)
    graph_dict = normalize_obj(mpld3_dict)
    
    return graph_dict


def convert_to_selectors(graph_selectors):
    keys = graph_selectors['keys']
    names = graph_selectors['names']
    defaults = graph_selectors['defaults']
    selectors = [
        {'key': key, 'name': name, 'checked': checked}
         for (key, name, checked) in zip(keys, names, defaults)]
    return selectors


def make_mpld3_graph_dict(result=None, which=None, zoom=None, startYear=None, endYear=None):
    """
    Converts an Optima sim Result into a dictionary containing
    mpld3 graph dictionaries and associated keys for display,
    which can be exported as JSON.

    Args:
        result: the Optima simulation Result object
        which: a list of keys to determine which plots to generate
        zoom: the relative size of the figure

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
        if 'advanced' not in which:
            advanced = False
            which = [w.split("-")[0] for w in which]
            def remove_duplicates(seq):
                seen = set()
                seen_add = seen.add
                return [x for x in seq if not (x in seen or seen_add(x))]
            which = remove_duplicates(which)
        else:
            advanced = True
            which.remove('advanced')

    print ">> make_mpld3_graph_dict advanced:", advanced

    graph_selectors = op.getplotselections(result, advanced=advanced)
    if advanced:
        normal_graph_selectors = op.getplotselections(result)
        n = len(normal_graph_selectors['keys'])
        normal_default_keys = []
        for i in range(n):
            if normal_graph_selectors["defaults"][i]:
                normal_default_keys.append(normal_graph_selectors["keys"][i])
        normal_default_keys = tuple(normal_default_keys)
        # rough and dirty defaults for missing defaults in advanced - convert 'numinci' to 'numinci-stacked', for example
        n = len(graph_selectors['keys'])
        for i in range(n):
            key = graph_selectors['keys'][i]
            if key.startswith(normal_default_keys) and ('stacked' in key) and ('numincibypop' not in key):
                graph_selectors['defaults'][i] = True
            if (key.split("-")[0] in which) and (('stacked' in key) and ('prev' not in key)):
                which[which.index(key.split("-")[0])] = key
        if 'prev' in which:
            which[which.index('prev')] = 'prev-population'
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

    graphs = op.makeplots(result, toplot=which, plotstartyear=startYear, plotendyear=endYear, newfig=True, die=False)
    op.reanimateplots(graphs)

    graph_selectors = []
    mpld3_graphs = []
    for g,graph_key in enumerate(graphs):
        graph_selectors.append(extract_graph_selector(graph_key))
#        graph_pos = 'mid' if type(graph_key)==str and graph_key.find('Care cascade')>=0 else None
        graph_pos = None
        graph_dict = convert_to_mpld3(graphs[graph_key], zoom=zoom, graph_pos=graph_pos)
        graph = graphs[graph_key]
        while len(graph.axes)>1:
            print('WARRRRRRRRRRRRRRRRRRRRRRRNING, too many axes')
            graph.delaxes(graph.axes[1])
        ylabels = [l.get_text() for l in graph.axes[0].get_yticklabels()]
        graph_dict['ylabels'] = ylabels
        xlabels = [l.get_text() for l in graph.axes[0].get_xticklabels()]
        graph_dict['xlabels'] = xlabels
        graph_dict['id'] = ('graph%i-' % g) + graph_dict['id'] # Prepend graph dict
        mpld3_graphs.append(graph_dict)
        print('TEMPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP')
        print(graph_key)
        print(graph_dict)

    return {
        'graphs': {
            "advanced": advanced,
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors,
            'resultId': str(result.uid),
        }
    }
