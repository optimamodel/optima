## Imports and globals...need Qt since matplotlib doesn't support edit boxes, grr!
from optima import dcp, printv, sigfig, plotepi, plotformatslist
from pylab import figure, close, floor, ion, axes, ceil, sqrt, array, isinteractive, ioff, show, transpose
from matplotlib.widgets import CheckButtons, Button
from PyQt4 import QtGui
global panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist, plotfig, panelfig, check, checkboxes, updatebutton, closebutton  # For manualfit GUI
if 1:  panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist, plotfig, panelfig, check, checkboxes, updatebutton, closebutton = [None]*16



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



def plotresults(results, toplot=None, fig=None, **kwargs):
    ''' 
    Like update() for pygui, but just open a new window
    Keyword arguments if supplied are passed on to figure().
    
    Usage:
        results = P.runsim('default')
        plotresults(results)
        
    Version: 1.1 (2016jan19) by cliffk
    '''
    if toplot is None: toplot = ['prev-tot', 'prev-per', 'numinci-sta']
    if fig is None: fig = figure('Optima results', facecolor=(1,1,1), **kwargs) # Create a figure based on supplied kwargs, if any
    nplots = len(toplot) # Calculate rows and columns of subplots
    nrows = int(ceil(sqrt(nplots)))
    ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
    
    # Do plotting
    wasinteractive = isinteractive()
    if wasinteractive: ioff()
    width,height = fig.get_size_inches()
    
    # Actually create plots
    plots = plotepi(results, which=toplot, figsize=(width, height))
    for p in range(len(plots)): addplot(fig, plots[p].axes[0], nrows, ncols, p+1)
    if wasinteractive: ion()
    show()





def closegui(event=None):
    ''' Close all GUI windows '''
    global plotfig, panelfig
    close(plotfig)
    close(panelfig)



def getchecked(check=None):
    ''' Return a list of whether or not each check box is checked or not '''
    ischecked = []
    for box in range(len(check.lines)): ischecked.append(check.lines[box][0].get_visible()) # Stupid way of figuring out if a box is ticked or not
    return ischecked
    
    
def update(event=None, tmpresults=None):
    ''' Close current window if it exists and open a new one based on user selections '''
    global plotfig, check, checkboxes, results
    if tmpresults is not None: results = tmpresults

    # If figure exists, get size, then close it
    try: width,height = plotfig.get_size_inches(); close(plotfig) # Get current figure dimensions
    except: width,height = 14,12 # No figure: use defaults
    
    # Get user selections
    ischecked = getchecked(check)
    toplot = array(checkboxes)[array(ischecked)].tolist() # Use logical indexing to get names to plot
    
    # Do plotting
    if sum(ischecked): # Don't do anything if no plots
        wasinteractive = isinteractive()
        if wasinteractive: ioff()
        plotfig = figure('Optima results', figsize=(width, height), facecolor=(1,1,1)) # Create figure with correct number of plots
        
        # Actually create plots
        plots = plotepi(results, which=toplot, figsize=(width, height))
        nplots = len(plots)
        nrows = int(ceil(sqrt(nplots)))
        ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
        for p in range(nplots): addplot(plotfig, plots[p].axes[0], nrows, ncols, p+1)
        if wasinteractive: ion()
        show()



def pygui(tmpresults, which=None):
    '''
    PYGUI
    
    Make a Python GUI for plotting results. Opens up a control window and a plotting window,
    and when "Update" is clicked, will clear the contents of the plotting window and replot.
    
    Usage:
        pygui(results, [which])
    
    where results is the output of e.g. runsim() and which is an optional list of form e.g.
        which = ['prev-tot', 'inci-pops']
    
    Warning: the plots won't resize automatically if the figure is resized, but if you click
    "Update", then they will.    
    
    Version: 1.1 (2015dec29) by cliffk
    '''
    global check, checkboxes, updatebutton, closebutton, panelfig, results
    results = tmpresults # Copy results to global variable    
    
    ## Define options for selection
    epikeys = results.main.keys()
    epinames = [thing.name for thing in results.main.values()]
    episubkeys = transpose(plotformatslist)[-1] # 'tot' = single overall value; 'per' = separate figure for each plot; 'sta' = stacked or multiline plot
    checkboxes = [] # e.g. 'prev-tot'
    checkboxnames = [] # e.g. 'HIV prevalence (%) -- total'
    for key in epikeys: # e.g. 'prev'
        for subkey in episubkeys: # e.g. 'tot'
            checkboxes.append(key+'-'+subkey)
    for name in epinames: # e.g. 'HIV prevalence'
        for subname in episubkeys: # e.g. 'total'
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
    panelfig = figure('Optima control panel', figsize=(7,8), facecolor=(0.95, 0.95, 0.95)) # Open control panel
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
    <html>
    <head><script src="https://code.jquery.com/jquery-1.11.3.min.js"></script></head>
    <body>
    !MAKE DIVS!
    <script>function mpld3_load_lib(url, callback){var s = document.createElement('script'); s.src = url; s.async = true; s.onreadystatechange = s.onload = callback; s.onerror = function(){console.warn("failed to load library " + url);}; document.getElementsByTagName("head")[0].appendChild(s)} mpld3_load_lib("https://mpld3.github.io/js/d3.v3.min.js", function(){mpld3_load_lib("https://mpld3.github.io/js/mpld3.v0.3git.js", function(){
    !DRAW FIGURES!
    })});
    </script>
    <script>
    function move_year() {
        console.log('trying to move year');
        var al = $('.mpld3-baseaxes').length;
        var dl = $('div.fig').length
        if (al === dl) {
            $('.mpld3-baseaxes > text').each(function() {
                var value = $(this).text();
                if (value === 'Year') {
                    console.log('found year');
                    $(this).attr('y', parseInt($(this).attr('y'))+10);
                    console.log($(this).attr('y'));
                }
            });
        } else {
            setTimeout(move_year, 150);
        }
    }
    function format_xaxis() {
        var axes = $('.mpld3-xaxis');
        var al = axes.length;
        var dl = $('div.fig').length;
        if (al === dl) {
            $(axes).find('g.tick > text').each(function() {
                $(this).text($(this).text().replace(',',''));
            });
        } else {
            setTimeout(format_xaxis, 150);
        }
    }
    function add_lines_to_legends() {
        console.log('adding lines to legends');
        var al = $('.mpld3-baseaxes').length;
        var dl = $('div.fig').length
        if (al === dl) {
            $('div.fig').each(function() {
                var paths = $(this).find('.mpld3-baseaxes > text');
                if (paths) {
                    var legend_length = paths.length - 2;
                    var lines = $(this).find('.mpld3-axes > path');
                    var lines_to_copy = lines.slice(lines.length - legend_length, lines.length);
                    $(this).find('.mpld3-baseaxes').append(lines_to_copy);
                }
            });
        } else {
            setTimeout(add_lines_to_legends, 150);
        }
    }
    $(document).ready(function() {
        format_xaxis();
        move_year();
        add_lines_to_legends();
    });
    </script>
    </body></html>
    '''

    ## Create the figures to plot
    jsons = [] # List for storing the converted JSONs
    plots = plotepi(results, which) # Generate the plots
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
        divstr += '<div style="%s" id="fig%i" class="fig"></div>\n' % (divstyle, p) # Add div information: key is unique ID for each figure
        jsonstr += 'mpld3.draw_figure("fig%i", %s);\n' % (p, jsons[p]) # Add the JSON representation of each figure -- THIS IS KEY!
    html = html.replace('!MAKE DIVS!',divstr) # Populate div information
    html = html.replace('!DRAW FIGURES!',jsonstr) # Populate figure information
    
    ## Launch a server or return the HTML representation
    if doplot: serve(html)
    else: return html





def manualfit(project=None, name='default', ind=0, verbose=4):
    ''' 
    Create a GUI for doing manual fitting via the backend. Opens up three windows: 
    results, results selection, and edit boxes.
    
    Current version only allows the user to modify force-of-infection, 
    
    Version: 1.0 (2015dec29) by cliffk
    '''
    
    ## Random housekeeping
    global panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
    fig = figure(); close(fig) # Open and close figure...dumb, no?
    ion() # We really need this here!
    nsigfigs = 3
    
    ## Initialize lists that do not initialize themselves
    boxes = []
    texts = []
    keylist = []
    namelist = []
    typelist = [] # Valid types are meta, pop, exp
    
    ## Get the list of parameters that can be fitted
    parset = dcp(project.parsets[name])
    tmppars = parset.pars[0]
    origpars = dcp(tmppars)

    for key in tmppars.keys():
        if hasattr(tmppars[key],'fittable'): # Don't worry if it doesn't work, not everything in tmppars is actually a parameter
            if tmppars[key].fittable is not 'no':
                keylist.append(key) # e.g. "initprev"
                namelist.append(tmppars[key].name) # e.g. "HIV prevalence"
                typelist.append(tmppars[key].fittable) # e.g. 'pop'
    nkeys = len(keylist) # Number of keys...note, this expands due to different populations etc.
    
    ## Convert to the full list of parameters to be fitted
    def populatelists():
        global tmppars, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
        fulllabellist = [] # e.g. "Initial HIV prevalence -- FSW"
        fullkeylist = [] # e.g. "initprev"
        fullsubkeylist = [] # e.g. "fsw"
        fulltypelist = [] # e.g. "pop"
        fullvallist = [] # e.g. 0.3
        for k in range(nkeys):
            key = keylist[k]
            if typelist[k]=='meta':
                fullkeylist.append(key)
                fullsubkeylist.append(None)
                fulltypelist.append(typelist[k])
                fullvallist.append(tmppars[key].m)
                fulllabellist.append(namelist[k] + ' -- meta')
            elif typelist[k]=='const':
                fullkeylist.append(key)
                fullsubkeylist.append(None)
                fulltypelist.append(typelist[k])
                fullvallist.append(tmppars[key].y)
                fulllabellist.append(namelist[k])
            elif typelist[k] in ['pop', 'pship']:
                for subkey in tmppars[key].y.keys():
                    fullkeylist.append(key)
                    fullsubkeylist.append(subkey)
                    fulltypelist.append(typelist[k])
                    fullvallist.append(tmppars[key].y[subkey])
                    fulllabellist.append(namelist[k] + ' -- ' + str(subkey))
            elif typelist[k]=='exp':
                for subkey in tmppars[key].p.keys():
                    fullkeylist.append(key)
                    fullsubkeylist.append(subkey)
                    fulltypelist.append(typelist[k])
                    fullvallist.append(tmppars[key].p[subkey][0])
                    fulllabellist.append(namelist[k] + ' -- ' + str(subkey))
            else:
                print('Parameter type "%s" not implemented!' % typelist[k])
    
    populatelists()
    nfull = len(fulllabellist) # The total number of boxes needed
    results = project.runsim(name)
    pygui(results)
    
    
    
    def closewindows():
        ''' Close all three open windows '''
        closegui()
        panel.close()
    
    
    ## Define update step
    def manualupdate():
        ''' Update GUI with new results '''
        global results, tmppars, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
        
        ## Loop over all parameters and update them
        for b,box in enumerate(boxes):
            if fulltypelist[b]=='meta': # Metaparameters
                key = fullkeylist[b]
                tmppars[key].m = eval(str(box.text()))
                printv('%s.m = %s' % (key, box.text()), 4, verbose=verbose)
            elif fulltypelist[b]=='pop' or fulltypelist[b]=='pship': # Populations or partnerships
                key = fullkeylist[b]
                subkey = fullsubkeylist[b]
                tmppars[key].y[subkey] = eval(str(box.text()))
                printv('%s.y[%s] = %s' % (key, subkey, box.text()), 4, verbose=verbose)
            elif fulltypelist[b]=='exp': # Population growth
                key = fullkeylist[b]
                subkey = fullsubkeylist[b]
                tmppars[key].p[subkey][0] = eval(str(box.text()))
                printv('%s.p[%s] = %s' % (key, subkey, box.text()), 4, verbose=verbose)
            if fulltypelist[b]=='const': # Metaparameters
                key = fullkeylist[b]
                tmppars[key].y = eval(str(box.text()))
                printv('%s.y = %s' % (key, box.text()), 4, verbose=verbose)
            else:
                print('Parameter type "%s" not implemented!' % fulltypelist[b])
        
        simparslist = parset.interp()
        results = project.runsim(simpars=simparslist)
        update(tmpresults=results)
        
    
    ## Keep the current parameters in the project; otherwise discard
    def keeppars():
        ''' Little function to reset origpars and update the project '''
        global origpars, tmppars, parset
        origpars = dcp(tmppars)
        parset.pars[0] = tmppars
        project.parsets[name].pars[0] = tmppars
        print('Parameters kept')
        return None
    
    
    def resetpars():
        ''' Reset the parameters to the last saved version '''
        global origpars, tmppars, parset
        tmppars = dcp(origpars)
        parset.pars[0] = tmppars
        populatelists()
        for i in range(nfull): boxes[i].setText(sigfig(fullvallist[i], sigfigs=nsigfigs))
        simparslist = parset.interp()
        results = project.runsim(simpars=simparslist)
        update(tmpresults=results)
        return None
    

    ## Set up GUI
    leftmargin = 10
    rowheight = 25
    colwidth = 500
    ncols = 3
    panelwidth = colwidth*ncols
    panelheight = rowheight*(nfull/ncols+2)+50
    buttonheight = panelheight-rowheight*1.5
    buttonoffset = panelwidth/ncols
    boxoffset = 300+leftmargin
    
    panel = QtGui.QWidget() # Create panel widget
    panel.setGeometry(100, 100, panelwidth, panelheight)
    for i in range(nfull):
        row = (i % floor((nfull+1)/ncols))+1
        col = floor(ncols*i/nfull)
        
        texts.append(QtGui.QLabel(parent=panel))
        texts[-1].setText(fulllabellist[i])
        texts[-1].move(leftmargin+colwidth*col, rowheight*row)
        
        boxes.append(QtGui.QLineEdit(parent = panel)) # Actually create the text edit box
        boxes[-1].move(boxoffset+colwidth*col, rowheight*row)
        boxes[-1].setText(sigfig(fullvallist[i], sigfigs=nsigfigs))
        boxes[-1].returnPressed.connect(manualupdate)
    
    keepbutton  = QtGui.QPushButton('Keep', parent=panel)
    resetbutton = QtGui.QPushButton('Reset', parent=panel)
    closebutton = QtGui.QPushButton('Close', parent=panel)
    
    keepbutton.move(0+buttonoffset, buttonheight)
    resetbutton.move(200+buttonoffset, buttonheight)
    closebutton.move(400+buttonoffset, buttonheight)
    
    keepbutton.clicked.connect(keeppars)
    resetbutton.clicked.connect(resetpars)
    closebutton.clicked.connect(closewindows)
    panel.show()