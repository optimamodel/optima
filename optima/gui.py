from pylab import axes, ceil, sqrt, array, figure, isinteractive, ion, ioff, close, show
from matplotlib.widgets import CheckButtons, Button
global controlfig, plotfig, check, button
plotfig = None

def gui(results):
    '''
    GUI
    
    Make a Python GUI for plotting results. Opens up a control window and a plotting window,
    and when "Update" is clicked, will clear the contents of the plotting window and replot.
    
    Usage:
    
    gui(results)
    
    Version: 2015dec08 by cliffk
    '''
    global controlfig, plotfig, check, button
    
    
    def getchecked(check):
        ''' Return a list of whether or not each check box is checked or not '''
        ischecked = []
        for box in range(len(check.lines)): ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
        return ischecked
    
    
    def addplot(thisfig, thisplot, nrows=1, ncols=1, n=1):
        ''' Add a plot to an existing figure '''
        thisfig._axstack.add(thisfig._make_key(thisplot), thisplot) # Add a plot to the axis stack
        thisplot.change_geometry(nrows, ncols, n) # Change geometry to be correct
        return None
        
    
    def update(event):
        ''' Close current window if it exists and open a new one based on user selections '''
        global plotfig
        
        # If figure exists, get size, then close it
        try: width,height = plotfig.get_size_inches(); close(plotfig) # Get current figure dimensions
        except: width,height = 8,6 # No figure: use defaults
        
        # Get user selections
        ischecked = getchecked(check)
        toplot = array(checkboxes)[array(ischecked)].tolist() # Use logical indexing to get names to plot
        nplots = sum(ischecked) # Calculate rows and columns of subplots
        nrows = int(ceil(sqrt(nplots)))
        ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
        
        # Do plotting
        if nplots>0: # Don't do anything if no plots
            wasinteractive = isinteractive()
            if wasinteractive: ioff()
            plotfig = figure(figsize=(width, height)) # Create figure with correct number of plots
            
            # Actually create plots
            plots = results.makeplots(toplot, figsize=(width, height))
            for p in range(len(plots)): addplot(plotfig, plots[p].axes[0], nrows, ncols, p+1)
            if wasinteractive: ion()
            show()
    
    
    ## Define options for selection
    epikeys = results.main.keys()
    episubkeys = ['tot','pops'] # Would be best not to hard-code this...
    checkboxes = []
    for key in epikeys:
        for subkey in episubkeys:
            checkboxes.append(key+'-'+subkey)
    nboxes = len(checkboxes)
    
    ## Set up control panel
    controlfig = figure(figsize=(4,8))
    checkboxaxes = axes([0.1, 0.15, 0.8, 0.8])
    buttonaxes = axes([0.1, 0.05, 0.8, 0.08])
    check = CheckButtons(checkboxaxes, checkboxes, [False]*nboxes)
    button = Button(buttonaxes, 'Update') 
    button.on_clicked(update) # Update figure if button is clicked