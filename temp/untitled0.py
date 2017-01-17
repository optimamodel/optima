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
    """A plugin to highlight lines on hover"""

    JAVASCRIPT = """
    mpld3.register_plugin("highlightarea", HighlightAreaPlugin);
    HighlightAreaPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    HighlightAreaPlugin.prototype.constructor = HighlightAreaPlugin;
    HighlightAreaPlugin.prototype.requiredProps = ["line_ids"];
    HighlightAreaPlugin.prototype.defaultProps = {alpha_bg:0.3, alpha_fg:1.0}
    function HighlightAreaPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    HighlightAreaPlugin.prototype.draw = function(){
      for(var i=0; i<this.props.line_ids.length; i++){
         var obj = mpld3.get_element(this.props.line_ids[i], this.fig),
             alpha_fg = this.props.alpha_fg;
             alpha_bg = this.props.alpha_bg;
         obj.elements()
             .on("mouseover", function(d, i){
                            d3.select(this).transition().duration(50)
                              .style("fill-opacity", alpha_fg);})
             .on("mouseout", function(d, i){
                            d3.select(this).transition().duration(200)
                              .style("fill-opacity", alpha_bg); });
      }
    };
    """
    
    JAVASCRIPT = '''
    mpld3.register_plugin("highlightarea", HighlightAreaPlugin);
    HighlightAreaPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    HighlightAreaPlugin.prototype.constructor = HighlightAreaPlugin;
    HighlightAreaPlugin.prototype.requiredProps = ["id"];
    HighlightAreaPlugin.prototype.defaultProps = {
        labels: null,
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
        var labels = this.props.labels;
        var color = this.props.color;
        var loc = this.props.location;
    
        this.highlightarea = this.fig.canvas.append("text")
            .attr("class", "mpld3-highlightarea-text")
            .attr("x", 0)
            .attr("y", 0)
            .text("")
            .style("visibility", "hidden");
    
        if (loc == "bottom left" || loc == "top left") {
            this.x = obj.ax.position[0] + 5 + this.props.hoffset;
            this.highlightarea.style("text-anchor", "beginning")
        } else if (loc == "bottom right" || loc == "top right") {
            this.x = obj.ax.position[0] + obj.ax.width - 5 + this.props.hoffset;
            this.highlightarea.style("text-anchor", "end");
        } else {
            this.highlightarea.style("text-anchor", "middle");
        }
    
        if (loc == "bottom left" || loc == "bottom right") {
            this.y = obj.ax.position[1] + obj.ax.height - 5 + this.props.voffset;
        } else if (loc == "top left" || loc == "top right") {
            this.y = obj.ax.position[1] + 5 + this.props.voffset;
        }
        
        function getMod(L, i) {
            return (L.length > 0) ? L[i % L.length] : null;
        }
        
        var schopenhauer = this
    
        schopenhauer.mouseover = function (d, i) {
            schopenhauer.highlightarea
                .style("visibility", "visible")
                .text((labels === null) ? "(" + d + ")" : getMod(labels, i));
            
            if (loc === "mouse") {
                var pos = d3.mouse(this.fig.canvas.node())
                schopenhauer.x = pos[0] + schopenhauer.props.hoffset;
                schopenhauer.y = pos[1] - schopenhauer.props.voffset;
            }
    
            schopenhauer.highlightarea
                .attr('x', schopenhauer.x)
                .attr('y', schopenhauer.y);
                
            console.log("ketchup");
            console.log(this);
            console.log("moocat");
            console.log(schopenhauer);
        }
    
        schopenhauer.mouseout = function (d, i) {
            schopenhauer.highlightarea.style("visibility", "hidden");
        }
    
        alpha_fg = schopenhauer.props.alpha_fg;
        alpha_bg = schopenhauer.props.alpha_bg;
        color = schopenhauer.props.color;
        
        schopenhauer.x = 600;
        schopenhauer.y = 300;
        
        var tooltip = d3.select("body")
            .append("div")
            .style("position", "absolute")
            .style("z-index", "10")
            .style("visibility", "hidden")
            .style("left", schopenhauer.x)
            .style("top", schopenhauer.y)
            .text("Missing label");
        
        obj.elements()
            .on("mouseover", function(d, i){
                            d3.select(this).transition().duration(50).style("fill-opacity", alpha_fg);
                            tooltip
                                .style("visibility", "visible")
                                .text(labels)
                                .style("color", color);
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
                      "labels": label,
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