import matplotlib.pyplot as plt
import numpy as np
from mpld3 import fig_to_html, plugins, show
fig, ax = plt.subplots()

N_paths = 50
N_steps = 100

x = np.linspace(0, 10, 100)
y = 0.1 * (np.random.random((N_paths, N_steps)) - 0.5)
y = y.cumsum(1)

fig, ax = plt.subplots(subplot_kw={'xticks': [], 'yticks': []})
lines = ax.plot(x, y.T, color='blue', lw=4, alpha=0.1)
labels = ['line %i' for i in range(N_paths)]

plugins.connect(fig, plugins.LineLabelTooltip(lines[0], labels))
fig_to_html(fig)
show()