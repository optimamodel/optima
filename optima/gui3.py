'''
GUI

Make a Python GUI for plotting results. Opens up a control window and a plotting window,
and when "Update" is clicked, will clear the contents of the plotting window and replot.

Version: 2015dec08 by cliffk
'''


## TEMP
print('Running GUI test...')
from optima import Project

P = Project(spreadsheet='test.xlsx')
results = P.runsim('default')
## /TEMP




#def gui(results):
from pylab import subplots, subplots_adjust, axes, ceil, sqrt, array, figure
from matplotlib.widgets import CheckButtons, Button

# Define options for selection
epikeys = results.main.keys()
episubkeys = ['tot','pops'] # Would be best not to hard-code this...
checkboxes = []
for key in epikeys:
    for subkey in episubkeys:
        checkboxes.append(key+'-'+subkey)
nboxes = len(checkboxes)

# Set up control panel
controlfig = figure(figsize=(4,8))
checkboxaxes = axes([0.1, 0.15, 0.8, 0.8])
buttonaxes = axes([0.1, 0.05, 0.8, 0.08])
check = CheckButtons(checkboxaxes, checkboxes, [False]*nboxes)
button = Button(buttonaxes, 'Update') 

# Set up results panel
plotfig = figure()


def getchecked(check):
    ''' Return a list of whether or not each check box is checked or not '''
    ischecked = []
    for box in range(len(check.lines)):
        ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
    return ischecked


def update(event):
    plotfig.clear() # Clear figure
    
    ischecked = getchecked(check)
    toplot = array(checkboxes)[array(ischecked)].tolist() # Use logical indexing to get names to plot
    
    # Calculate rows and columns of subplots
    nplots = sum(ischecked)
    nrows = int(ceil(sqrt(nplots)))
    ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
    
    # Do plotting
    if nplots>0: # Don't do anything if no plots
        width,height = plotfig.get_size_inches()
        tmpfig, fakeaxes = subplots(ncols, nrows, sharex='all', figsize=(height, width)) # Create figure with correct number of plots
        close(tmpfig) # Close unneeded figure
        if wasinteractive: ion()
#        for fa in array(fakeaxes).flatten(): fig._axstack.remove(fa) # Remove placeholder axes
        
        # Actually create plots
        plots = results.makeplots(toplot, figsize=(width, height))

        for p in range(len(plots)):
            thisplot = plots[p].axes[0]
            plotfig._axstack.add(plotfig._make_key(thisplot), thisplot)
            thisplot.change_geometry(nrows,ncols,p+1)
#            currentaxes.append(thisplot)

# Update figure if button is clicked
button.on_clicked(update)