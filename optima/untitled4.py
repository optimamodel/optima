from pylab import *

import numpy as np, matplotlib.pyplot as plt
import mpld3
import json


ion()


#mpld3.enable_notebook()

def create_plot():
    fig, ax = plt.subplots(figsize=(12,4))

    n = 100
    x = np.linspace(0, 10, n)
    l1 = ax.plot(x, np.sin(x)+randn(n), label='sin', lw=3, alpha=1)
    l2 = ax.plot(x, np.cos(x)+randn(n), label='cos', lw=3, alpha=1)
    l3 = ax.plot(x[::5], 0.5 * np.sin(x[::5] + 2), 'ob', label='dots',
                 alpha=1)

    labels = ['sin', 'cos', 'dots']
    interactive_legend = mpld3.plugins.InteractiveLegendPlugin([l1, l2, l3], labels, start_visible=[1, 0, True])
    mpld3.plugins.connect(fig, interactive_legend)

    ax.set_title("Interactive legend test", size=20)
    plt.subplots_adjust(right=.5)
    return fig

fig1 = create_plot()
fig2 = create_plot()
#mpld3.show()


#html = '''
#<script type="text/javascript" src="http://d3js.org/d3.v3.min.js"></script>
#<script type="text/javascript" src="http://mpld3.github.io/js/mpld3.v0.2.js"></script>
#<style>
#</style>
#<div id="fig01"></div>
#<div id="fig02"></div>
#<script type="text/javascript">
#  var json01 = {<snip1>};
#  var json02 = {<snip1>};
#  mpld3.draw_figure("fig01", json01);
#  mpld3.draw_figure("fig02", json02);
#</script>
#'''
#
#json01 = json.dumps(mpld3.fig_to_dict(fig1))
#json02 = json.dumps(mpld3.fig_to_dict(fig2))
#html.replace('{<snip1}',json01)
#html.replace('{<snip2}',json02)

html = mpld3.fig_to_html(fig1)


mpld3._server.serve(html, ip='127.0.0.1', port=8888, n_retries=50, files=None, open_browser=True, http_server=None)

