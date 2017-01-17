"""
PLOTUTILS

This file stores plotting utilities -- for adjusting the ticks, MPLD3 properties, etc.

Version: 2017jan17
"""

from optima import OptimaException, gridcolormap
from pylab import fill_between, rand, figure, arange
from mpld3 import plugins, utils, show as d3show
from matplotlib import ticker

def SItickformatter(x, pos):  # formatter function takes tick label and tick position
    ''' Formats axis ticks so that e.g. 34,243 becomes 34K '''
    if abs(x)>=1e9:     output = str(x/1e9)+'B'
    elif abs(x)>=1e6:   output = str(x/1e6)+'M'
    elif abs(x)>=1e3:   output = str(x/1e3)+'K'
    else:               output = str(x)
    return output

def SIticks(figure, axis='y'):
    ''' Apply SI tick formatting to the y axis of a figure '''
    for ax in figure.axes:
        if axis=='x':   thisaxis = ax.xaxis
        elif axis=='y': thisaxis = ax.yaxis
        elif axis=='z': thisaxis = ax.zaxis
        else: raise OptimaException('Axis must be x, y, or z')
        thisaxis.set_major_formatter(ticker.FuncFormatter(SItickformatter))

def commaticks(figure, axis='y'):
    ''' Use commas in formatting the y axis of a figure -- see http://stackoverflow.com/questions/25973581/how-to-format-axis-number-format-to-thousands-with-a-comma-in-matplotlib '''
    for ax in figure.axes:
        if axis=='x':   thisaxis = ax.xaxis
        elif axis=='y': thisaxis = ax.yaxis
        elif axis=='z': thisaxis = ax.zaxis
        else: raise OptimaException('Axis must be x, y, or z')
        thisaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

def rgb2hex(colors):
    """Return color as #rrggbb for the given color values."""
    return '#%02x%02x%02x' % tuple([int(round(col*255)) for col in colors])


class HighlightArea(plugins.PluginBase):
    """A plugin to highlight areas on hover"""
    
    JAVASCRIPT = '''
    mpld3.register_plugin("highlightarea", HighlightAreaPlugin);
    HighlightAreaPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    HighlightAreaPlugin.prototype.constructor = HighlightAreaPlugin;
    HighlightAreaPlugin.prototype.requiredProps = ["id"];
    HighlightAreaPlugin.prototype.defaultProps = {
        label: 'Missing label',
        color: '#000000',
        hoffset: 0,
        voffset: 10,
        location: 'mouse',
        alpha_bg: 0.7,
        alpha_fg: 1.0
        
    };
    
    function HighlightAreaPlugin(fig, props) {
        mpld3.Plugin.call(this, fig, props);
    }
    
    HighlightAreaPlugin.prototype.draw = function() {
        var obj = mpld3.get_element(this.props.id, this.fig);
        var label = this.props.label;
        var color = this.props.color;
        var loc = this.props.location;
        alpha_fg = this.props.alpha_fg;
        alpha_bg = this.props.alpha_bg;
    
        var xpos = 600;
        var ypos = 300;
        
        var tooltip = d3.select("body")
            .append("div")
            .style("position", "absolute")
            .style("z-index", "10")
            .style("visibility", "hidden")
            .style("left", xpos)
            .style("top", ypos)
            .text("Missing label");
        
        obj.elements()
            .on("mouseover", function(d, i){
                            d3.select(this).transition().duration(50).style("fill-opacity", alpha_fg);
                            tooltip
                                .style("visibility", "visible")
                                .style("color", color)
                                .text(label);
                            })
             .on("mouseout", function(d, i){
                            d3.select(this).transition().duration(200).style("fill-opacity", alpha_bg);
                            tooltip.style("visibility", "hidden");
                            });
    }
''' 



    def __init__(self, area, label=None, color=None):
        self.dict_ = {"type": "highlightarea",
                      "id": utils.get_id(area),
                      "label": label,
                      "color": color,
                      "alpha_bg": 0.7,
                      "alpha_fg": 1.0}


def highlightareasplugin(fig=None, areas=None, labels=None, colors=None):
    ''' Helper function to make it easier to use the plugin '''
    for i in range(len(areas)):
        highlightarea = HighlightArea(areas[i], label=labels[i], color=rgb2hex(colors[i]))
        plugins.connect(fig, highlightarea) 
    return None


def highlightdemo():
    n = 50
    m = 5
    fig = figure()
    lower = rand(n)
    areas = []
    labels = []
    colors = gridcolormap(m)
    for i in range(m):
        upper = rand(n)
        tmp = fill_between(arange(n), lower, lower+upper, facecolor=colors[i], alpha=0.8, lw=0)
        lower += upper
        areas.append(tmp)
        labels.append('Value: %0.5f'%rand())
    
    highlightareasplugin(fig, areas, labels, colors)
    d3show()