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


class CKTest(plugins.PluginBase):
    """A plugin to highlight lines on hover"""

    JAVASCRIPT = """
    mpld3.register_plugin("cktest", CKTestPlugin);
    CKTestPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    CKTestPlugin.prototype.constructor = CKTestPlugin;
    CKTestPlugin.prototype.requiredProps = ["line_ids"];
    CKTestPlugin.prototype.defaultProps = {alpha_bg:0.3, alpha_fg:1.0}
    function CKTestPlugin(fig, props){
        mpld3.Plugin.call(this, fig, props);
    };

    CKTestPlugin.prototype.draw = function(){
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
    mpld3.register_plugin("ckhighlight", CKTestPlugin);
    CKTestPlugin.prototype = Object.create(mpld3.Plugin.prototype);
    CKTestPlugin.prototype.constructor = CKTestPlugin;
    CKTestPlugin.prototype.requiredProps = ["id"];
    CKTestPlugin.prototype.defaultProps = {
        labels: null,
        hoffset: 0,
        voffset: 10,
        location: 'mouse',
        alpha_bg: 0.7,
        alpha_fg: 1.0
    };
    
    function CKTestPlugin(fig, props) {
        mpld3.Plugin.call(this, fig, props);
    }
    
    CKTestPlugin.prototype.draw = function() {
        var obj = mpld3.get_element(this.props.id, this.fig);
        var labels = this.props.labels;
        var loc = this.props.location;
    
        alpha_fg = schopenhauer.props.alpha_fg;
        alpha_bg = schopenhauer.props.alpha_bg;
        
        var tooltip = d3.select("body")
            .append("div")
            .style("position", "absolute")
            .style("z-index", "10")
            .style("visibility", "hidden")
            .text("a simple tooltip");
        
        obj.elements()
            .on("mouseover", function(d, i){
                            d3.select(this).transition().duration(50).style("fill-opacity", alpha_fg);
                            
                            var pos = d3.mouse(this.fig.canvas.node())
                            var xpos = pos[0] + this.props.hoffset;
                            var ypos = pos[1] - this.props.voffset;
                            
                            tooltip
                                .style("visibility", "visible")
                                .style("left", xpos)
                                .style("top", ypos);
                            })
             .on("mouseout", function(d, i){
                            d3.select(this).transition().duration(200).style("fill-opacity", alpha_bg);
                            tooltip.style("visibility", "hidden");
                            });
    }
''' 


    def __init__(self, area, label=None,
                 hoffset=0, voffset=10, location="mouse"):
        if location not in ["bottom left", "top left", "bottom right",
                            "top right", "mouse"]:
            raise ValueError("invalid location: {0}".format(location))
        self.dict_ = {"type": "ckhighlight",
                      "id": utils.get_id(area),
                      "labels": label if label is None else [label],
                      "hoffset": hoffset,
                      "voffset": voffset,
                      "location": location,
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
    tmp = fill_between(arange(n), a, a+b, facecolor=colors[i], alpha=0.8, lw=0, label='%i'%i)
    a = a+b
    areas.append(tmp)



#plugins.connect(fig, CKTest(areas))
for i in range(len(areas)):
    ckhighlight = CKTest(areas[i], '%i'%i)
    plugins.connect(fig, ckhighlight) 
d3show()