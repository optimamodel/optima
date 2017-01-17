"""
Visualizing Random Walks
========================
This shows the use of transparent lines to visualize random walk data.
Thre is also a custom plugin defined which causes lines to be highlighted
when the mouse hovers over them.
Use the toolbar buttons at the bottom-right of the plot to enable zooming
and panning, and to reset the view.
"""

from pylab import fill_between, rand, figure, arange
from mpld3 import plugins, utils, show as d3show
from optima import gridcolormap

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

n = 50
m = 5
fig = figure()
a = rand(n)
areas = []
colors = gridcolormap(m)
for i in range(m):
    b = rand(n)
    tmp = fill_between(arange(n), a, a+b, facecolor=colors[i], alpha=0.8, lw=0)
    a = a+b
    areas.append(tmp)


for i in range(len(areas)):
    highlightarea = HighlightArea(areas[i], label='%0.5f'%rand(), color=rgb2hex(colors[i]))
    plugins.connect(fig, highlightarea) 
d3show()