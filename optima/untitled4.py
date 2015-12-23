from pylab import *

import numpy as np, matplotlib.pyplot as plt
import mpld3


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
#fig2 = create_plot()
mpld3.show()

