from optima import epiplot
from pylab import axes, ceil, sqrt, array, figure, isinteractive, ion, ioff, close, show
from matplotlib.widgets import CheckButtons, Button

global plotfig, panelfig, check, updatebutton, closebutton # Without these, interactivity doesn't work
plotfig = None # Initialize plot figure
panelfig = None # Initialize panel figure


def addplot(thisfig, thisplot, nrows=1, ncols=1, n=1):
    ''' Add a plot to an existing figure '''
    thisfig._axstack.add(thisfig._make_key(thisplot), thisplot) # Add a plot to the axis stack
    thisplot.change_geometry(nrows, ncols, n) # Change geometry to be correct
    orig = thisplot.get_position() # get the original position 
    widthfactor = 0.9/ncols**(1/4.)
    heightfactor = 0.9/nrows**(1/4.)
    pos2 = [orig.x0, orig.y0,  orig.width*widthfactor, orig.height*heightfactor] 
    thisplot.set_position(pos2) # set a new position

    return None



def gui(results, which=None):
    '''
    GUI
    
    Make a Python GUI for plotting results. Opens up a control window and a plotting window,
    and when "Update" is clicked, will clear the contents of the plotting window and replot.
    
    Usage:
        gui(results, [which])
    
    where results is the output of e.g. runsim() and which is an optional list of form e.g.
        which = ['prev-tot', 'inci-pops']
    
    Warning: the plots won't resize automatically if the figure is resized, but if you click
    "Update", then they will.    
    
    Version: 1.1 (2015dec29) by cliffk
    '''
    global check, updatebutton, closebutton, panelfig
    
    
    def getchecked(check):
        ''' Return a list of whether or not each check box is checked or not '''
        ischecked = []
        for box in range(len(check.lines)): ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
        return ischecked
    
    
    def update(event):
        ''' Close current window if it exists and open a new one based on user selections '''
        global plotfig

        # If figure exists, get size, then close it
        try: width,height = plotfig.get_size_inches(); close(plotfig) # Get current figure dimensions
        except: width,height = 14,12 # No figure: use defaults
        
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
            plotfig = figure(figsize=(width, height), facecolor=(1,1,1)) # Create figure with correct number of plots
            
            # Actually create plots
            plots = epiplot(results, which=toplot, figsize=(width, height))
            for p in range(len(plots)): addplot(plotfig, plots[p].axes[0], nrows, ncols, p+1)
            if wasinteractive: ion()
            show()
    
    def closegui(event):
        ''' Close all GUI windows '''
        global plotfig, panelfig
        close(plotfig)
        close(panelfig)
    
    
    ## Define options for selection
    epikeys = results.main.keys()
    epinames = [thing.name for thing in results.main.values()]
    episubkeys = ['tot','pops'] # Would be best not to hard-code this...
    episubnames = ['total', 'by population']
    checkboxes = [] # e.g. 'prev-tot'
    checkboxnames = [] # e.g. 'HIV prevalence (%) -- total'
    for key in epikeys: # e.g. 'prev'
        for subkey in episubkeys: # e.g. 'tot'
            checkboxes.append(key+'-'+subkey)
    for name in epinames: # e.g. 'HIV prevalence'
        for subname in episubnames: # e.g. 'total'
            checkboxnames.append(name+' -- '+subname)
    nboxes = len(checkboxes) # Number of choices
    
    ## Set up what to plot when screen first opens
    truebydefault = 2 # Number of boxes to check true by default
    if which is None: # No inputs: set the first couple true by default
        defaultchecks = truebydefault*[True]+[False]*(nboxes-truebydefault)
    else: # They're specified
        defaultchecks = []
        for name in checkboxes: # Check to see if they match
            if name in which: defaultchecks.append(True)
            else: defaultchecks.append(False)
            
    ## Set up control panel
    try: fc = results.project.settings.optimablue # Try loading global optimablue
    except: fc = (0.16, 0.67, 0.94) # Otherwise, just specify it :)
    panelfig = figure(figsize=(7,8), facecolor=(0.95, 0.95, 0.95)) # Open control panel
    checkboxaxes = axes([0.1, 0.15, 0.8, 0.8]) # Create checkbox locations
    updateaxes = axes([0.1, 0.05, 0.3, 0.05]) # Create update button location
    closeaxes  = axes([0.6, 0.05, 0.3, 0.05]) # Create close button location
    check = CheckButtons(checkboxaxes, checkboxnames, defaultchecks) # Actually create checkboxes
    for label in check.labels: # Loop over each checkbox
        thispos = label.get_position() # Get their current location
        label.set_position((thispos[0]*0.5,thispos[1])) # Not sure why by default the check boxes are so far away
    updatebutton = Button(updateaxes, 'Update', color=fc) # Make button pretty and blue
    closebutton = Button(closeaxes, 'Close', color=fc) # Make button pretty and blue
    updatebutton.on_clicked(update) # Update figure if button is clicked
    closebutton.on_clicked(closegui) # Close figures
    update(None) # Plot initially










def browser(results, which=None, doplot=True):
    ''' 
    Create an MPLD3 GUI and display in the browser. This is basically a testbed for 
    the Optima frontend.
    
    Usage:
        browser(results, [which])
    
    where results is the output of e.g. runsim() and which is an optional list of form e.g.
        which = ['prev-tot', 'inci-pops']
    
    With doplot=True, launch a web server. Otherwise, return the HTML representation of the figures.
    
    Version: 1.1 (2015dec29) by cliffk
    '''
    import mpld3 # Only import this if needed, since might not always be available
    import json
    if doplot: from webserver import serve # For launching in a browser

    wasinteractive = isinteractive() # Get current state of interactivity so the screen isn't flooded with plots
    if wasinteractive: ioff()
    
    
    ## Specify the div style, and create the HTML template we'll add the data to
    divstyle = "float: left"
    html = '''
    <html><body>
    !MAKE DIVS!
    <script>function mpld3_load_lib(url, callback){var s = document.createElement('script'); s.src = url; s.async = true; s.onreadystatechange = s.onload = callback; s.onerror = function(){console.warn("failed to load library " + url);}; document.getElementsByTagName("head")[0].appendChild(s)} mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
    !DRAW FIGURES!
    })});
    </script></body></html>
    '''

    ## Create the figures to plot
    jsons = [] # List for storing the converted JSONs
    plots = epiplot(results, which) # Generate the plots
    nplots = len(plots) # Figure out how many plots there are
    for p in range(nplots): # Loop over each plot
        fig = figure() # Create a blank figure
        addplot(fig, plots[p].axes[0]) # Add this plot to this figure
        mpld3.plugins.connect(fig, mpld3.plugins.MousePosition(fontsize=14,fmt='.4r')) # Add plugins
        jsons.append(str(json.dumps(mpld3.fig_to_dict(fig)))) # Save to JSON
        close(fig) # Close
    
    ## Create div and JSON strings to replace the placeholers above
    divstr = ''
    jsonstr = ''
    for p in range(nplots):
        divstr += '<div style="%s" id="fig%i"></div>\n' % (divstyle, p) # Add div information: key is unique ID for each figure
        jsonstr += 'mpld3.draw_figure("fig%i", %s);\n' % (p, jsons[p]) # Add the JSON representation of each figure -- THIS IS KEY!
    html = html.replace('!MAKE DIVS!',divstr) # Populate div information
    html = html.replace('!DRAW FIGURES!',jsonstr) # Populate figure information
    
    ## Launch a server or return the HTML representation
    if doplot: serve(html)
    else: return html