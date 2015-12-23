from pylab import *

import numpy as np, matplotlib.pyplot as plt
import mpld3
import json

html = '''
<html><body>
!MAKE DIVS!
<script>function mpld3_load_lib(url, callback){var s = document.createElement('script'); s.src = url; s.async = true; s.onreadystatechange = s.onload = callback; s.onerror = function(){console.warn("failed to load library " + url);}; document.getElementsByTagName("head")[0].appendChild(s)} mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
!DRAW FIGURES!
})});
</script></body></html>
'''


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



nplots = 4

figs = []
jsons = []
for p in range(nplots): 
    figs.append(create_plot())
    jsons.append(str(json.dumps(mpld3.fig_to_dict(figs[-1]))))

divstr = ''
jsonstr = ''
for p in range(nplots):
    divstr += '<div id="fig%i"></div>\n' % p
    jsonstr += 'mpld3.draw_figure("fig%i", %s);\n' % (p, jsons[p])

html = html.replace('!MAKE DIVS!',divstr)
html = html.replace('!DRAW FIGURES!',jsonstr)

mpld3._server.serve(html, ip='127.0.0.1', port=8888, n_retries=50, files=None, open_browser=True, http_server=None)

