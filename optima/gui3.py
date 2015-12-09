'''
GUI

Make a Python GUI for plotting results. Opens up a control window and a plotting window,
and when "Update" is clicked, will clear the contents of the plotting window and replot.

Version: 2015dec08 by cliffk
'''

print('Running GUI test...')
from optima import Project

P = Project(spreadsheet='test.xlsx')
results = P.runsim('default')



#def gui(results):
from pylab import subplots, subplots_adjust, axes, ceil, sqrt, array
from matplotlib.widgets import CheckButtons
global currentaxes

# Define options for selection
epikeys = results.main.keys()
episubkeys = ['tot','pops'] # Would be best not to hard-code this...
checkboxes = []
for key in epikeys:
    for subkey in episubkeys:
        checkboxes.append(key+'-'+subkey)
nboxes = len(checkboxes)

fig, currentaxes = subplots()
if type(currentaxes)!=list: currentaxes = [currentaxes]
subplots_adjust(right=0.5)
rax = axes([0.82, 0.05, 0.17, 0.9])

check = CheckButtons(rax, checkboxes, [False]*nboxes)


def getchecked(check):
    ''' Return a list of whether or not each check box is checked or not '''
    ischecked = []
    for box in range(len(check.lines)):
        ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
    return ischecked

def update(label):
    global currentaxes
    ischecked = getchecked(check)
    toplot = array(checkboxes)[array(ischecked)].tolist() # Use logical indexing to get names to plot
    
    # Calculate rows and columns of subplots
    nplots = sum(ischecked)
    nrows = int(ceil(sqrt(nplots)))
    ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
    
    print('hi!')
    print nplots
    
    for ax in currentaxes:
        fig._axstack.remove(ax)
    currentaxes = []
    
    # Do plotting
    if nplots>0: # Don't do anything if no plots
        width,height = fig.get_size_inches()
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
            currentaxes.append(thisplot)


check.on_clicked(update)