from pylab import *

import numpy as np, matplotlib.pyplot as plt
import mpld3
import json


ion()


#mpld3.enable_notebook()

#def create_plot():
#    fig, ax = plt.subplots(figsize=(12,4))
#
#    n = 100
#    x = np.linspace(0, 10, n)
#    l1 = ax.plot(x, np.sin(x)+randn(n), label='sin', lw=3, alpha=1)
#    l2 = ax.plot(x, np.cos(x)+randn(n), label='cos', lw=3, alpha=1)
#    l3 = ax.plot(x[::5], 0.5 * np.sin(x[::5] + 2), 'ob', label='dots',
#                 alpha=1)
#
#    labels = ['sin', 'cos', 'dots']
#    interactive_legend = mpld3.plugins.InteractiveLegendPlugin([l1, l2, l3], labels, start_visible=[1, 0, True])
#    mpld3.plugins.connect(fig, interactive_legend)
#
#    ax.set_title("Interactive legend test", size=20)
#    plt.subplots_adjust(right=.5)
#    return fig
#
#fig1 = create_plot()
#fig2 = create_plot()
#mpld3.show()


html = '''
<html><head><title>mpld3 plot</title></head><body>


<style>

</style>

<div id="fig_el66921396654576636326433896759"></div>
<script>
function mpld3_load_lib(url, callback){
  var s = document.createElement('script');
  s.src = url;
  s.async = true;
  s.onreadystatechange = s.onload = callback;
  s.onerror = function(){console.warn("failed to load library " + url);};
  document.getElementsByTagName("head")[0].appendChild(s);
}

if(typeof(mpld3) !== "undefined" && mpld3._mpld3IsLoaded){
   // already loaded: just create the figure
   !function(mpld3){
       
       mpld3.draw_figure("fig_el66921396654576636326433896759", {"axes": [{"xlim": [0.0, 1.0], "yscale": "linear", "axesbg": "#FFFFFF", "texts": [], "zoomable": true, "images": [], "xdomain": [0.0, 1.0], "ylim": [3.0, 5.0], "paths": [], "sharey": [], "sharex": [], "axesbgalpha": null, "axes": [{"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "bottom", "nticks": 6, "tickvalues": null}, {"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "left", "nticks": 5, "tickvalues": null}], "lines": [{"color": "#0000FF", "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 2, "alpha": 1, "xindex": 0, "linewidth": 1.0, "data": "data01", "id": "el6692139665197662544"}], "markers": [], "id": "el6692139665215857744", "ydomain": [3.0, 5.0], "collections": [], "xscale": "linear", "bbox": [0.125, 0.099999999999999978, 0.77500000000000002, 0.80000000000000004]}], "height": 480.0, "width": 640.0, "plugins": [{"type": "reset"}, {"enabled": false, "button": true, "type": "zoom"}, {"enabled": false, "button": true, "type": "boxzoom"}], "data": {"data01": [[0.0, 3.0], [1.0, 5.0]]}, "id": "el6692139665457663632"});
   }(mpld3);
}else if(typeof define === "function" && define.amd){
   // require.js is available: use it to load d3/mpld3
   require.config({paths: {d3: "https://mpld3.github.io/js/d3.v3.min"}});
   require(["d3"], function(d3){
      window.d3 = d3;
      mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
         
         mpld3.draw_figure("fig_el66921396654576636326433896759", {"axes": [{"xlim": [0.0, 1.0], "yscale": "linear", "axesbg": "#FFFFFF", "texts": [], "zoomable": true, "images": [], "xdomain": [0.0, 1.0], "ylim": [3.0, 5.0], "paths": [], "sharey": [], "sharex": [], "axesbgalpha": null, "axes": [{"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "bottom", "nticks": 6, "tickvalues": null}, {"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "left", "nticks": 5, "tickvalues": null}], "lines": [{"color": "#0000FF", "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 2, "alpha": 1, "xindex": 0, "linewidth": 1.0, "data": "data01", "id": "el6692139665197662544"}], "markers": [], "id": "el6692139665215857744", "ydomain": [3.0, 5.0], "collections": [], "xscale": "linear", "bbox": [0.125, 0.099999999999999978, 0.77500000000000002, 0.80000000000000004]}], "height": 480.0, "width": 640.0, "plugins": [{"type": "reset"}, {"enabled": false, "button": true, "type": "zoom"}, {"enabled": false, "button": true, "type": "boxzoom"}], "data": {"data01": [[0.0, 3.0], [1.0, 5.0]]}, "id": "el6692139665457663632"});
      });
    });
}else{
    // require.js not available: dynamically load d3 & mpld3
    mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){
         mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
                 
                 mpld3.draw_figure("fig_el66921396654576636326433896759", {"axes": [{"xlim": [0.0, 1.0], "yscale": "linear", "axesbg": "#FFFFFF", "texts": [], "zoomable": true, "images": [], "xdomain": [0.0, 1.0], "ylim": [3.0, 5.0], "paths": [], "sharey": [], "sharex": [], "axesbgalpha": null, "axes": [{"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "bottom", "nticks": 6, "tickvalues": null}, {"scale": "linear", "tickformat": null, "grid": {"gridOn": false}, "fontsize": 12.0, "position": "left", "nticks": 5, "tickvalues": null}], "lines": [{"color": "#0000FF", "yindex": 1, "coordinates": "data", "dasharray": "none", "zorder": 2, "alpha": 1, "xindex": 0, "linewidth": 1.0, "data": "data01", "id": "el6692139665197662544"}], "markers": [], "id": "el6692139665215857744", "ydomain": [3.0, 5.0], "collections": [], "xscale": "linear", "bbox": [0.125, 0.099999999999999978, 0.77500000000000002, 0.80000000000000004]}], "height": 480.0, "width": 640.0, "plugins": [{"type": "reset"}, {"enabled": false, "button": true, "type": "zoom"}, {"enabled": false, "button": true, "type": "boxzoom"}], "data": {"data01": [[0.0, 3.0], [1.0, 5.0]]}, "id": "el6692139665457663632"});
            })
         });
}
</script></body></html>
'''
#
#json01 = json.dumps(mpld3.fig_to_dict(fig1))
#json02 = json.dumps(mpld3.fig_to_dict(fig2))
#html.replace('{<snip1}',json01)
#html.replace('{<snip2}',json02)


#plot([3,5])
#fig1 = gcf()
#
#html = mpld3.fig_to_html(fig1)


mpld3._server.serve(html, ip='127.0.0.1', port=8888, n_retries=50, files=None, open_browser=True, http_server=None)

