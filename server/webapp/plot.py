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

    mpld3_dict = mpld3.fig_to_dict(figure) # !~! most likely the yticklabels are getting lost here, could be related to https://stackoverflow.com/a/37277515 perhaps
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

def process_which(result=None, which=None, advanced=None, includeadvancedtracking=False):
    """
    Takes in the which given by the frontend and processes 'default', 'advanced' etc

    Args:
        result: the Optima simulation Result object, must not be None
        which: a list of keys to determine which plots to generate

    Returns:
        which: A list of graphs to be plotted without plot type if not advanced,
            with plot type if advanced
        selectors: All currently available graph selectors
        advanced: boolean if advanced
        originalwhich: the original list
    """
    origwhich = op.dcp(which)
    if advanced is not None and advanced:
        which.append('advanced')

    if which is None:
        advanced = False
        if hasattr(result, 'which'):
            which = result.which
            if which is None:
                which = {}
            print(">> process_which has cache:", which)
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

    print(">> process_which advanced:", advanced)

    graph_selectors = op.getplotselections(result, advanced=advanced,includeadvancedtracking=includeadvancedtracking)
    if advanced:
        # This changes the which keys without a type '-stacked' for example to follow that in getdefaultplots()
        for wi, which_key in enumerate(which):
            if which_key == 'advanced' or which_key == 'default':  # advanced should be removed already but just to be sure
                continue
            if which_key.find('-') == -1:  # '-' not found
                for i, key in enumerate(graph_selectors['keys']):
                    if graph_selectors['defaults'][i] and key.startswith(which_key) and (key not in which):
                        which[wi] = key  # note that if both 'numinci-stacked' and 'numinci-population' for example are in getdefaultplots(), there may be some bugs

        # the rest of the which keys without a type default to '-stacked' in the below code, unless it is prev -> prev-population

        # rough and dirty defaults for missing defaults in advanced - convert 'numinci' to 'numinci-stacked', for example
        n = len(graph_selectors['keys'])
        for i in range(n):
            key = graph_selectors['keys'][i]
            if (key.split("-")[0] in which) and (('stacked' in key) and ('prev' not in key)):
                which[which.index(key.split("-")[0])] = key     # All plots default to stacked except prev

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

    return which,selectors,advanced,origwhich

import sciris as sc
def make_mpld3_graph_dict(result=None, which=None, zoom=None, startYear=None, endYear=None, includeadvancedtracking=False):
    """
    Converts an Optima sim Result into a dictionary containing
    mpld3 graph dictionaries and associated keys for display,
    which can be exported as JSON.

    Args:
        result: the Optima simulation Result object, must not be None
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
    start = sc.tic()
    which, selectors, advanced,origwhich = process_which(result=result,which=which, includeadvancedtracking=includeadvancedtracking)

    print(">> make_mpld3_graph_dict which:", which)
    print(">> make_mpld3_graph_dict times starting", sc.toc(start=start, output=True, doprint=False))
    graphs = op.makeplots(result, toplot=which, plotstartyear=startYear, plotendyear=endYear, newfig=True, die=False)
    print(">> make_mpld3_graph_dict times madeplots", sc.toc(start=start, output=True, doprint=False))
    op.reanimateplots(graphs)
    print(">> make_mpld3_graph_dict times reanimated", sc.toc(start=start, output=True, doprint=False))

    graph_selectors = []
    mpld3_graphs = []
    times = []
    start2 = sc.tic()
    for g,graph_key in enumerate(graphs):
        graph_selectors.append(extract_graph_selector(graph_key))
        times.append(sc.toc(start=start2, output=True, doprint=False))
        start2 = sc.tic()
        graph_pos = None
        graph_dict = convert_to_mpld3(graphs[graph_key], zoom=zoom, graph_pos=graph_pos) # !~! most likely the yticklabels are getting lost here
        times.append(sc.toc(start=start2, output=True, doprint=False))
        start2 = sc.tic()
        graph = graphs[graph_key]
        while len(graph.axes)>1:
            print('Warning, too many axes, attempting removal')
            graph.delaxes(graph.axes[1])
        ylabels = [l.get_text() for l in graph.axes[0].get_yticklabels()]
        graph_dict['ylabels'] = ylabels
        xlabels = [l.get_text() for l in graph.axes[0].get_xticklabels()]
        graph_dict['xlabels'] = xlabels
        graph_dict['id'] = ('graph%i-' % g) + graph_dict['id'] # Prepend graph dict
        mpld3_graphs.append(graph_dict)
        times.append(sc.toc(start=start2, output=True, doprint=False))
        start2 = sc.tic()
        times.append('')
    print(">> make_mpld3_graph_dict times made dicts", sc.toc(start=start, output=True, doprint=False))
    print(">> make_mpld3_graph_dict times made dicts", times)
    return {
        'graphs': {
            "advanced": advanced,
            "mpld3_graphs": mpld3_graphs,
            "selectors": selectors,
            'graph_selectors': graph_selectors,
            'resultId': str(result.uid),
        }
    }
