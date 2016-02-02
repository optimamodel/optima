## Imports and globals...need Qt since matplotlib doesn't support edit boxes, grr!
from optima import OptimaException, dcp, printv, sigfig, makeplots, getplotselections, gridcolormap, odict
from pylab import figure, close, floor, ion, axes, ceil, sqrt, array, isinteractive, ioff, show, pause
from pylab import subplot, xlabel, ylabel, transpose, legend, fill_between, xlim
from matplotlib.widgets import CheckButtons, Button
global panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist, plotfig, panelfig, check, checkboxes, updatebutton, closebutton  # For manualfit GUI
if 1:  panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist, plotfig, panelfig, check, checkboxes, updatebutton, closebutton = [None]*16



def addplot(thisfig, thisplot, name=None, nrows=1, ncols=1, n=1):
    ''' Add a plot to an existing figure '''
    thisfig._axstack.add(thisfig._make_key(thisplot), thisplot) # Add a plot to the axis stack
    thisplot.change_geometry(nrows, ncols, n) # Change geometry to be correct
    orig = thisplot.get_position() # get the original position 
    widthfactor = 0.9/ncols**(1/4.)
    heightfactor = 0.9/nrows**(1/4.)
    pos2 = [orig.x0, orig.y0,  orig.width*widthfactor, orig.height*heightfactor] 
    thisplot.set_position(pos2) # set a new position
    return None



def plotresults(results, toplot=None, fig=None, **kwargs): # WARNING, should kwargs be for figure() or makeplots()???
    ''' 
    Does the hard work for updateplots() for pygui()
    Keyword arguments if supplied are passed on to figure().
    
    Usage:
        results = P.runsim('default')
        plotresults(results)
        
    Version: 1.3 (2016jan25) by cliffk
    '''
    
    if 'figsize' not in kwargs: kwargs['figsize'] = (14,10) # Default figure size
    if fig is None: fig = figure(facecolor=(1,1,1), **kwargs) # Create a figure based on supplied kwargs, if any
    
    # Do plotting
    wasinteractive = isinteractive()
    if wasinteractive: ioff()
    width,height = fig.get_size_inches()
    
    # Actually create plots
    plots = makeplots(results, toplot=toplot, die=True, figsize=(width, height))
    nplots = len(plots)
    nrows = int(ceil(sqrt(nplots)))  # Calculate rows and columns of subplots
    ncols = nrows-1 if nrows*(nrows-1)>=nplots else nrows
    for p in range(len(plots)): 
        naxes = len(plots[p].axes)
        if naxes==1: # Usual situation: just plot the normal axis
            addplot(fig, plots[p].axes[0], name=plots.keys()[p], nrows=nrows, ncols=ncols, n=p+1)
        elif naxes>1: # Multiple axes, e.g. allocation bar plots -- have to do some maths to figure out where to put the plots
            origrow = floor(p/ncols)
            origcol = p%ncols # Column doesn't change
            newnrows = nrows*naxes
            newrowstart = naxes*origrow # e.g. 2 axes in 3rd row = 5th row in new system
            for a in range(naxes):
                thisrow = newrowstart+a # Increment rows
                newp = ncols*thisrow + origcol # Calculate new row/column
                addplot(fig, plots[p].axes[a], name=plots.keys()[p], nrows=int(newnrows), ncols=int(ncols), n=int(newp+1))
        else: pass # Must have 0 length or something
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
    
    
def updateplots(event=None, tmpresults=None):
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
        plotfig = figure('Optima results', figsize=(width, height), facecolor=(1,1,1)) # Create figure with correct number of plots
        plotresults(results, toplot=toplot, fig=plotfig, figsize=(width, height))
    
    return None



def pygui(tmpresults, toplot=None):
    '''
    PYGUI
    
    Make a Python GUI for plotting results. Opens up a control window and a plotting window,
    and when "Update" is clicked, will clear the contents of the plotting window and replot.
    
    Usage:
        pygui(results, [toplot])
    
    where results is the output of e.g. runsim() and toplot is an optional list of form e.g.
        toplot = ['prev-tot', 'inci-per']
    
    Warning: the plots won't resize automatically if the figure is resized, but if you click
    "Update", then they will.    
    
    Version: 1.2 (2016jan25)
    '''
    global check, checkboxes, updatebutton, closebutton, panelfig, results
    results = tmpresults # Copy results to global variable    
    
    ## Define options for selection
    plotselections = getplotselections(results)
    checkboxes = plotselections['keys']
    checkboxnames = plotselections['names']
    defaultchecks = plotselections['defaults']
    
    ## Set up control panel
    figwidth = 7
    figheight = 1+len(checkboxes)*0.35 # Scale dynamically based on how many options are available
    try: fc = results.project.settings.optimablue # Try loading global optimablue
    except: fc = (0.16, 0.67, 0.94) # Otherwise, just specify it :)
    panelfig = figure(num='Optima control panel', figsize=(figwidth,figheight), facecolor=(0.95, 0.95, 0.95)) # Open control panel
    checkboxaxes = axes([0.1, 0.15, 0.8, 0.8]) # Create checkbox locations
    updateaxes = axes([0.1, 0.05, 0.3, 0.05]) # Create update button location
    closeaxes  = axes([0.6, 0.05, 0.3, 0.05]) # Create close button location
    check = CheckButtons(checkboxaxes, checkboxnames, defaultchecks) # Actually create checkboxes
    for label in check.labels: # Loop over each checkbox
        thispos = label.get_position() # Get their current location
        label.set_position((thispos[0]*0.5,thispos[1])) # Not sure why by default the check boxes are so far away
    updatebutton = Button(updateaxes, 'Update', color=fc) # Make button pretty and blue
    closebutton = Button(closeaxes, 'Close', color=fc) # Make button pretty and blue
    updatebutton.on_clicked(updateplots) # Update figure if button is clicked
    closebutton.on_clicked(closegui) # Close figures
    updateplots(None) # Plot initially










def browser(results, toplot=None, doplot=True):
    ''' 
    Create an MPLD3 GUI and display in the browser. This is basically a testbed for 
    the Optima frontend.
    
    Usage:
        browser(results, [toplot])
    
    where results is the output of e.g. runsim() and toplot is an optional list of form e.g.
        toplot = ['prev-tot', 'inci-per']
    
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
    plots = makeplots(results=results, toplot=toplot) # Generate the plots
    nplots = len(plots) # Figure out how many plots there are
    for p in range(nplots): # Loop over each plot
        fig = figure() # Create a blank figure
        naxes = len(plots[p].axes)
        for ax in range(naxes): addplot(fig, plots[p].axes[ax], name=plots.keys()[p], nrows=naxes, n=ax+1) # Add this plot to this figure
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









def manualfit(project=None, name='default', ind=0, verbose=2):
    ''' 
    Create a GUI for doing manual fitting via the backend. Opens up three windows: 
    results, results selection, and edit boxes.
    
    Current version only allows the user to modify force-of-infection, 
    
    Version: 1.0 (2015dec29) by cliffk
    '''
    
    # For edit boxes, we need this -- but import it here so only this function will fail
    from PyQt4 import QtGui
    
    ## Random housekeeping
    global panel, results, origpars, tmppars, parset, fulllabellist, fullkeylist, fullsubkeylist, fulltypelist, fullvallist
    fig = figure(); close(fig) # Open and close figure...dumb, no? Otherwise get "QWidget: Must construct a QApplication before a QPaintDevice"
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
                printv('Parameter type "%s" not implemented!' % typelist[k], 2, verbose)
    
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
                printv('%s.m = %s' % (key, box.text()), 3, verbose)
            elif fulltypelist[b]=='pop' or fulltypelist[b]=='pship': # Populations or partnerships
                key = fullkeylist[b]
                subkey = fullsubkeylist[b]
                tmppars[key].y[subkey] = eval(str(box.text()))
                printv('%s.y[%s] = %s' % (key, subkey, box.text()), 3, verbose)
            elif fulltypelist[b]=='exp': # Population growth
                key = fullkeylist[b]
                subkey = fullsubkeylist[b]
                tmppars[key].p[subkey][0] = eval(str(box.text()))
                printv('%s.p[%s] = %s' % (key, subkey, box.text()), 3, verbose)
            elif fulltypelist[b]=='const': # Metaparameters
                key = fullkeylist[b]
                tmppars[key].y = eval(str(box.text()))
                printv('%s.y = %s' % (key, box.text()), 3, verbose)
            else:
                printv('Parameter type "%s" not implemented!' % fulltypelist[b], 2, verbose)
        
        simparslist = parset.interp()
        results = project.runsim(simpars=simparslist)
        updateplots(tmpresults=results)
        
    
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
        updateplots(tmpresults=results)
        return None
    

    ## Set up GUI
    leftmargin = 10
    rowheight = 25
    colwidth = 500
    ncols = 3
    nrows = ceil(nfull/float(ncols))
    panelwidth = colwidth*ncols
    panelheight = rowheight*(nfull/ncols+2)+50
    buttonheight = panelheight-rowheight*1.5
    buttonoffset = panelwidth/ncols
    boxoffset = 300+leftmargin
    
    panel = QtGui.QWidget() # Create panel widget
    panel.setGeometry(100, 100, panelwidth, panelheight)
    spottaken = [] # Store list of existing entries, to avoid duplicates
    for i in range(nfull):
        row = (i % nrows) + 1
        col = floor(i/float(nrows))
        spot = (row,col)
        if spot in spottaken: 
            errormsg = 'Cannot add a button to %s since there already is one!' % str(spot)
            raise OptimaException(errormsg)
        else: spottaken.append(spot)
        
        texts.append(QtGui.QLabel(parent=panel))
        texts[-1].setText(fulllabellist[i])
        texts[-1].move(leftmargin+colwidth*col, rowheight*row)
        
        boxes.append(QtGui.QLineEdit(parent = panel)) # Actually create the text edit box
        boxes[-1].move(boxoffset+colwidth*col, rowheight*row)
        printv('Setting up GUI checkboxes: %s' % [i, fulllabellist[i], boxoffset+colwidth*col, rowheight*row], 4, verbose)
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





def plotpeople(project=None, people=None, start=2, end=None, pops=None, animate=True, verbose=2, figsize=(16,10), **kwargs):
    '''
    A function to plot all people as a stacked plot
    
    "Exclude" excludes the first N health states -- useful for excluding susceptibles.
    
    Usage example:
        import optima as op
        P = op.defaults.defaultproject('simple')
        P.runsim()
        people = P.results[-1].raw[0]['people']
        op.gui.plotpeople(P, people)
    
    Version: 2016jan30
    '''
    if pops is None: pops = Ellipsis # This is a slice
    legendsettings = {'loc':'upper left', 'bbox_to_anchor':(1.02, 1), 'fontsize':11, 'title':''}
    nocolor = (0.9,0.9,0.9)
    labels = project.settings.statelabels
    
    plotstyles = odict([
    ('uncirc', ('|','|')), 
    ('circ',   ('+','|')), 
    ('undx',   ('.','o')), 
    ('dx',     ('*','*')), 
    ('care',   ('O','o')), 
    ('usvl',   ('-','|')), 
    ('svl',    ('x','|')), 
    ('lost',   ('O','o')), 
    ('off',    ('*','*'))])
    
    hatchstyles = []
    linestyles = []
    for key in plotstyles.keys():
        hatchstyles.extend([plotstyles[key][0] for lab in labels if lab.startswith(key)])
        linestyles.extend([plotstyles[key][1]  for lab in labels if lab.startswith(key)])
    
    labels = labels[start:end]
    hatchstyles = hatchstyles[start:end]
    linestyles = linestyles[start:end]
    
    ppl = people[start:end,:,:] # Exclude initial people
    ppl = ppl[:,pops,:] # Filter selected populations
    ppl = ppl[:,:,:].sum(axis=1) # Sum over people
    ppl = transpose(ppl) # So time is plotted on x-axis
    
    nstates = len(labels)
    colors = gridcolormap(nstates)
    tvec = project.settings.maketvec() # WARNING, won't necessarily match this ppl
    bottom = 0*tvec
    figure(facecolor=(1,1,1), figsize=figsize, **kwargs)
    ax = subplot(111)
    xlim((tvec[0], tvec[-1]))
    for st in range(nstates-1,-1,-1):
        this = ppl[:,st]
        if sum(this): thiscolor = colors[st]
        else: thiscolor = nocolor
        printv('State: %i/%i Hatch: %s Line: %s Color: %s' % (st, nstates, hatchstyles[st], linestyles[st], thiscolor), 4, verbose)
        fill_between(tvec, bottom, this+bottom, facecolor=thiscolor, alpha=1, lw=0, hatch=hatchstyles[st])
        bottom += this
        
        # Legend stuff
        xlabel('Year')
        ylabel('Number of people')
        ax.plot((0, 0), (0, 0), color=thiscolor, linewidth=10, label=labels[st], marker=linestyles[st]) # This loop is JUST for the legends! since fill_between doesn't count as a plot object, stupidly... -- WARNING, copied from plotepi()
        handles, legendlabels = ax.get_legend_handles_labels()
        legend(reversed(handles), reversed(legendlabels), **legendsettings)
        if animate:
            show()
            pause(0.1)
    
    return None
    






global plotparsbacktbut, plotparsnextbut, plotparslider
def plotpars(parslist=None, verbose=2, figsize=(16,12), **kwargs):
    '''
    A function to plot all parameters. 'pars' can be an odict or a list of pars odicts.
    
    Version: 2016jan30
    '''
    from optima import Par, makesimpars
    from numpy import array, vstack
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, Slider
    
    global position, plotparsbacktbut, plotparsnextbut, plotparslider
    position = 0
    
    if type(parslist)!=list: parslist = [parslist] # Convert to list
    
    
    allplotdata = []
    for pars in parslist:
        count = 0
        simpars = makesimpars(pars)
        tvec = simpars['tvec']
        plotdata = array([['name','simpar','par_t', 'par_y']], dtype=object) # Set up array for holding plotting results
        for i,key1 in enumerate(pars):
            par = pars[key1]
            if isinstance(par, Par):
                if   hasattr(par,'y'): pardata = par.y # WARNING, add par.m as well?
                elif hasattr(par,'p'): pardata = par.p # Population size
                else: raise Exception('???')
                if hasattr(pardata, 'keys') and len(pardata.keys())>0: # Only ones that don't have a len are temp pars
                    nkeys = len(pardata.keys())
                    for k,key2 in enumerate(pardata.keys()):
                        if hasattr(par, 't'): t = par.t[key2]
                        else: t = tvec[0] # For a constant
                        count += 1
                        if nkeys==1: thissimpar = simpars[key1]
                        else: thissimpar = simpars[key1][k]
                        thisplot = array(['%3i. %s - %s' % (count-1, key1, key2), thissimpar, t, pardata[key2]], dtype=object)
                        if array(thissimpar).sum()==0: thisplot[0] += ' (zero)'
                        plotdata = vstack([plotdata, thisplot])
                else:
                    t = tvec[0] # For a constant
                    count += 1
                    thisplot = array(['%3i. %s' % (count-1, key1), simpars[key1], t, pardata], dtype=object)
                    plotdata = vstack([plotdata, thisplot])
        plotdata = plotdata[1:,:] # Remove header
        allplotdata.append(plotdata)
    
    
    ## Do plotting
    nplots = len(plotdata)
    if any([len(pltd)!=nplots for pltd in allplotdata]): 
        printv('Warning, not all pars are the same length, only plotting first', 2, verbose)
        allplotdata = allplotdata[0]
    nrows = 5
    ncols = 4
    nperscreen = nrows*ncols

    plotparsfig = plt.figure(facecolor=(0.9,0.9,0.9), figsize=figsize)
    plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.95, wspace=0.2, hspace=0.4)
    plotparsaxs = []
    count = 0
    for row in range(nrows):
        for col in range(ncols):
            count += 1
            plotparsaxs.append(plotparsfig.add_subplot(nrows, ncols, count))
    
    backframe = plotparsfig.add_axes([0.1, 0.03, 0.1, 0.03])
    sliderframe = plotparsfig.add_axes([0.3, 0.03, 0.4, 0.03])
    nextframe = plotparsfig.add_axes([0.8, 0.03, 0.1, 0.03])
    plotparsbackbut = Button(backframe, 'Back')
    plotparsnextbut = Button(nextframe, 'Next')
    plotparslider = Slider(sliderframe, '', 0, nplots, valinit=0, valfmt='%d')
    
    def updateb(event=None): 
        global position
        position -= nperscreen
        position = max(0,position)
        position = min(nplots-nperscreen, position)
        plotparslider.set_val(position)
        update(position)
    
    def updaten(event=None): 
        global position
        position += nperscreen
        position = max(0,position)
        position = min(nplots-nperscreen, position)
        plotparslider.set_val(position)
        update(position)
    
    def update(tmp=0):
        global position, plotparslider
        position = tmp
        position = max(0,position)
        position = min(nplots-nperscreen, position)
        for i,ax in enumerate(plotparsaxs):
            ax.cla()
            ax.hold(True)
            nplt = i+position
            if nplt<nplots:
                for pd,plotdata in enumerate(allplotdata):
                    try:
                        this = plotdata[nplt,:]
                        ax.set_title(this[0])
                        if   isinstance(this[1], (int, float)):   ax.plot(tvec, 0*tvec+this[1])
                        elif len(this[1])==0:                     ax.set_title(this[0]+' is empty')
                        elif len(this[1])==1:                     ax.plot(tvec, 0*tvec+this[1])
                        elif len(this[1])==len(tvec):             ax.plot(tvec, this[1])
                        else: pass # Population size, doesn't use control points
                    except: print('??????')
                    try: 
                        if not(hasattr(this[3],'__len__') and len(this[3])==0): ax.scatter(this[2],this[3])
                    except Exception: pass # print('Problem with "%s": "%s"' % (this[0], E.message))
                    if pd==len(allplotdata)-1: # Do this for the last plot only
                        ax.set_ylim((0,1.1*ax.get_ylim()[1]))
                        ax.set_xlim((tvec[0],tvec[-1]))
                
    update()
    plotparsbackbut.on_clicked(updateb)
    plotparsnextbut.on_clicked(updaten)
    plotparslider.on_changed(update)
    return allplotdata