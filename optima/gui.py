from optima import epiplot
from pylab import axes, ceil, sqrt, array, figure, isinteractive, ion, ioff, close, show
from matplotlib.widgets import CheckButtons, Button
global plotfig, check, button # Without these, interactivity doesn't work
plotfig = None # Initialize plot figure


def addplot(thisfig, thisplot, nrows=1, ncols=1, n=1):
    ''' Add a plot to an existing figure '''
    thisfig._axstack.add(thisfig._make_key(thisplot), thisplot) # Add a plot to the axis stack
    thisplot.change_geometry(nrows, ncols, n) # Change geometry to be correct
    orig = thisplot.get_position() # get the original position 
    factor = 0.3+nrows**(1/3.)
    pos2 = [orig.x0, orig.y0,  orig.width/factor, orig.height] 
    thisplot.set_position(pos2) # set a new position

    return None
        

def gui(results):
    '''
    GUI
    
    Make a Python GUI for plotting results. Opens up a control window and a plotting window,
    and when "Update" is clicked, will clear the contents of the plotting window and replot.
    
    Usage:
        gui(results)
    
    Warning: the plots won't resize automatically if the figure is resized, but if you click
    "Update", then they will.    
    
    Version: 2015dec23 by cliffk
    '''
    global check, button
    
    
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
            plotfig = figure(figsize=(width, height), facecolor=(1,1,1)) # Create figure with correct number of plots
            
            # Actually create plots
            plots = epiplot(results, toplot, figsize=(width, height))
            for p in range(len(plots)): addplot(plotfig, plots[p].axes[0], nrows, ncols, p+1)
            if wasinteractive: ion()
            show()
    
    
    ## Define options for selection
    epikeys = results.main.keys()
    epinames = [thing.name for thing in results.main.values()]
    episubkeys = ['tot','pops'] # Would be best not to hard-code this...
    episubnames = ['total', 'by population']
    checkboxes = []
    checkboxnames = []
    for key in epikeys:
        for subkey in episubkeys:
            checkboxes.append(key+'-'+subkey)
    for name in epinames:
        for subname in episubnames:
            checkboxnames.append(name+' -- '+subname)
    nboxes = len(checkboxes)
    
    ## Set up control panel
    try: fc = results.project.settings.optimablue
    except: fc = (0.16, 0.67, 0.94)
    figure(figsize=(7,8), facecolor=(0.95, 0.95, 0.95))
    checkboxaxes = axes([0.1, 0.15, 0.8, 0.8])
    buttonaxes = axes([0.1, 0.05, 0.8, 0.08])
    defaultchecks = [True]+[False]*(nboxes-1)
    check = CheckButtons(checkboxaxes, checkboxnames, defaultchecks)
    for label in check.labels:
        thispos = label.get_position()
        label.set_position((thispos[0]*0.5,thispos[1])) # not sure why by default the check boxes are so far away
    button = Button(buttonaxes, 'Update', color=fc) 
    button.on_clicked(update) # Update figure if button is clicked
    update(None) # Plot initially










def browser(results):
    ''' Create an mpld3 GUI '''
    import mpld3
    import json

    wasinteractive = isinteractive() # Get current state of interactivity
    if wasinteractive: ioff()
    
    divstyle = "float: left; border: solid 1px black;"
    
    html = '''
    <html><body>
    !MAKE DIVS!
    <script>function mpld3_load_lib(url, callback){var s = document.createElement('script'); s.src = url; s.async = true; s.onreadystatechange = s.onload = callback; s.onerror = function(){console.warn("failed to load library " + url);}; document.getElementsByTagName("head")[0].appendChild(s)} mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
    !DRAW FIGURES!
    })});
    </script></body></html>
    '''

    figs = []
    jsons = []
    plots = epiplot(results)
    nplots = len(plots)
    for p in range(nplots): 
        figs.append(figure())
        addplot(figs[-1], plots[p].axes[0])
        mpld3.plugins.connect(figs[-1], mpld3.plugins.MousePosition(fontsize=14)) # Add plugins
        jsons.append(str(json.dumps(mpld3.fig_to_dict(figs[-1])))) # Save to JSON
        close(figs[-1])
    
    divstr = ''
    jsonstr = ''
    for p in range(nplots):
        divstr += '<div style="%s" id="fig%i"></div>\n' % (divstyle, p)
        jsonstr += 'mpld3.draw_figure("fig%i", %s);\n' % (p, jsons[p])
    
    html = html.replace('!MAKE DIVS!',divstr)
    html = html.replace('!DRAW FIGURES!',jsonstr)
    
    mpld3._server.serve(html, ip='127.0.0.1', port=8888, n_retries=50, files=None, open_browser=True, http_server=None)
