print('Running GUI test...')
from optima import Project

P = Project(spreadsheet='test.xlsx')
results = P.runsim('default')



#def gui(results):
from pylab import subplots, subplots_adjust, axes, ceil, sqrt, close, isinteractive, ion, ioff, array
from matplotlib.widgets import CheckButtons

# Define options for selection
epikeys = results.main.keys()
episubkeys = ['tot','pops'] # Would be best not to hard-code this...
checkboxes = []
for key in epikeys:
    for subkey in episubkeys:
        checkboxes.append(key+'-'+subkey)
nboxes = len(checkboxes)

fig, tmp = subplots()
fig._axstack.remove(tmp)
subplots_adjust(right=0.8)
rax = axes([0.82, 0.05, 0.17, 0.9])

check = CheckButtons(rax, checkboxes, [False]*nboxes)


def getchecked(check):
    ''' Return a list of whether or not each check box is checked or not '''
    ischecked = []
    for box in range(len(check.lines)):
        ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
    return ischecked

def update(label):
    ischecked = getchecked(check)
    toplot = array(checkboxes)[array(ischecked)].tolist() # Use logical indexing to get names to plot
    
    # Calculate rows and columns of subplots
    nplots = sum(ischecked)
    nrows = int(ceil(sqrt(nplots)))
    ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
    
    # Do plotting
    if nplots>0: # Don't do anything if no plots
#        wasinteractive = isinteractive()
#        if wasinteractive: ioff()
        height,width = fig.get_size_inches()
#        fig, fakeaxes = subplots(ncols, nrows, sharex='all', figsize=(height, width)) # Create figure with correct number of plots
#        close(fig) # Close unneeded figure
#        if wasinteractive: ion()
#        for fa in array(fakeaxes).flatten(): fig._axstack.remove(fa) # Remove placeholder axes
        
        # Actually create plots
        plots = results.makeplots(toplot, figsize=(width, height))

        for p in range(len(plots)):
            thisplot = plots[p].axes[0]
            fig._axstack.add(fig._make_key(thisplot), thisplot)
            thisplot.change_geometry(nrows,ncols,p+1)
#    else:
#        fig = figure() # Blank figure


check.on_clicked(update)

#import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.widgets import CheckButtons
#
#t = np.arange(0.0, 2.0, 0.01)
#s0 = np.sin(2*np.pi*t)
#s1 = np.sin(4*np.pi*t)
#s2 = np.sin(6*np.pi*t)
#
#
#
#
#def func(label):
#    isticked = []
#    for box in range(len(check.lines)):
#        isticked.append(check.lines[box][0].get_visible())
#    
#    ax.cla()
#    if isticked[0]: ax.plot(t, s0, lw=2)
#    if isticked[1]: ax.plot(t, s1, lw=2)
#    if isticked[2]: ax.plot(t, s2, lw=2)
#
#    plt.draw()
#check.on_clicked(func)
#
#plt.show()