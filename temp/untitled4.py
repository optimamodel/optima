import numpy as np
import mpld3, pandas as pd

#df = pd.DataFrame(np.cumsum(np.random.normal(0,1,(5,1000)),axis=1).T)
#axes = df.plot(figsize=(14,4), colormap='spectral');
#
#labels = list(df.columns.values)
#for i in range(len(labels)):
#    tooltip = mpld3.plugins.LineLabelTooltip(axes.get_lines()[i], labels[i])
#    mpld3.plugins.connect(plt.gcf(), tooltip) 
#
#mpld3.show()



import matplotlib.pyplot as plt

N_paths = 50
N_steps = 100

x = np.linspace(0, 10, 100)
y = 0.1 * (np.random.random((N_paths, N_steps)) - 0.5)
y = y.cumsum(1)

fig, ax = plt.subplots(subplot_kw={'xticks': [], 'yticks': []})
lines = ax.plot(x, y.T, color='blue', lw=4, alpha=0.1)

for i in range(len(lines)):
    tooltip = mpld3.plugins.LineLabelTooltip(lines[i], '%i'%i)
    mpld3.plugins.connect(plt.gcf(), tooltip) 

mpld3.show()