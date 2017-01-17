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
    
        this.ckhighlight = this.fig.canvas.append("text")
            .attr("class", "mpld3-ckhighlight-text")
            .attr("x", 0)
            .attr("y", 0)
            .text("")
            .style("visibility", "hidden");
    
        if (loc == "bottom left" || loc == "top left") {
            this.x = obj.ax.position[0] + 5 + this.props.hoffset;
            this.ckhighlight.style("text-anchor", "beginning")
        } else if (loc == "bottom right" || loc == "top right") {
            this.x = obj.ax.position[0] + obj.ax.width - 5 + this.props.hoffset;
            this.ckhighlight.style("text-anchor", "end");
        } else {
            this.ckhighlight.style("text-anchor", "middle");
        }
    
        if (loc == "bottom left" || loc == "bottom right") {
            this.y = obj.ax.position[1] + obj.ax.height - 5 + this.props.voffset;
        } else if (loc == "top left" || loc == "top right") {
            this.y = obj.ax.position[1] + 5 + this.props.voffset;
        }
        
        function getMod(L, i) {
            return (L.length > 0) ? L[i % L.length] : null;
        }
    
        function mouseover(d, i) {
            this.ckhighlight
                .style("visibility", "visible")
                .text((labels === null) ? "(" + d + ")" : getMod(labels, i));
        }
    
        function mousemove(d, i) {
            if (loc === "mouse") {
                var pos = d3.mouse(this.fig.canvas.node())
                this.x = pos[0] + this.props.hoffset;
                this.y = pos[1] - this.props.voffset;
            }
    
            this.ckhighlight
                .attr('x', this.x)
                .attr('y', this.y);
        }
    
        function mouseout(d, i) {
            this.ckhighlight.style("visibility", "hidden");
        }
    
        obj.elements()
            .on("mouseover", mouseover.bind(this))
            .on("mousemove", mousemove.bind(this))
            .on("mouseout", mouseout.bind(this));
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