from pylab import *

import numpy as np, matplotlib.pyplot as plt
import mpld3
import json



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


html = '''
<html><body>
<div id="fig01"></div>
<div id="fig02"></div>
<script>function mpld3_load_lib(url, callback){var s = document.createElement('script'); s.src = url; s.async = true; s.onreadystatechange = s.onload = callback; s.onerror = function(){console.warn("failed to load library " + url);}; document.getElementsByTagName("head")[0].appendChild(s)} mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
mpld3.draw_figure("fig01", {<snip1>});
mpld3.draw_figure("fig02", {<snip2>});
})});
</script></body></html>
'''



json01 = str(json.dumps(mpld3.fig_to_dict(fig1)))
json02 = str(json.dumps(mpld3.fig_to_dict(fig2)))
html = html.replace('{<snip1>}',json01)
html = html.replace('{<snip2>}',json02)


#plot([3,5])
#fig1 = gcf()
#
#html = mpld3.fig_to_html(fig1)


mpld3._server.serve(html, ip='127.0.0.1', port=8888, n_retries=50, files=None, open_browser=True, http_server=None)

