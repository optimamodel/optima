def viewuncerresults(E, whichgraphs={'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'force':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1], 'costann':[0,1], 'costcum':[0,1], 'commit':[0,1]}, simstartyear=2000, simendyear=2030, onefig=True, verbose=2, show_wait=False, linewidth=2):
    """
    Generate all outputs required for the model, including prevalence, incidence,
    deaths, etc.
    Version: 2015jan18
    """
    
    from matplotlib.pylab import figure, plot, hold, scatter, xlabel, ylabel, xlim, ylim, legend, title, ndim, ceil, sqrt, subplot, show, fill_between
    from printv import printv

    
    npops = len(E['prev']['pops']) # Calculate number of populations
    
    if onefig:
        figh = figure(figsize=(24,16), facecolor='w')
        figh.subplots_adjust(left=0.04) # Less space on left
        figh.subplots_adjust(right=0.99) # Less space on right
        figh.subplots_adjust(top=0.98) # Less space on bottom
        figh.subplots_adjust(bottom=0.04) # Less space on bottom
        figh.subplots_adjust(wspace=0.5) # More space between
        figh.subplots_adjust(hspace=0.5) # More space between
        nplots = onefig
        for graph in whichgraphs.keys():
            for i in range(len(whichgraphs[graph])):
                if graph[0:4] != 'cost': nplots += whichgraphs[graph][i]*[npops,1][i]
                else: nplots += whichgraphs[graph][i]
        nxplots = ceil(sqrt(nplots))
        nyplots = nxplots
        while nxplots*nyplots>nplots: nyplots -= 1
        if nxplots*nyplots<nplots: nyplots += 1
    
    count = 0
    whichgraphkeys = whichgraphs.keys()
    whichgraphkeys.sort()
    for graph in whichgraphkeys: # Loop over each type of data, e.g. prevalence
        epigraph = (graph[0:4] not in ['comm', 'cost']) # Flag for whether or not it's an epi graph vs. a cost graph
        for popstot in range(2): # Loop over population or total graphs
            if whichgraphs[graph][popstot]:
                printv('Plotting graph %s...' % graph, 4, verbose)
                
                if popstot==0 and epigraph: # Population graphs for epi data
                    for p in range(npops):
                        if onefig:
                            count += 1
                            subplot(nxplots, nyplots, count)
                        else:
                            figure(facecolor='w')
                        hold(True)
                        fill_between(E['tvec'], E[graph]['pops'][p]['low'], E[graph]['pops'][p]['high'], alpha=0.2, edgecolor='none')
                        plot(E['tvec'], E[graph]['pops'][p]['best'], c=E['colorm'], linewidth=linewidth)
                        if ndim(E[graph]['ydata'])==2:
                            scatter(E['xdata'], E[graph]['ydata'][p], c=E['colord'])
                        
                        title(E[graph]['pops'][p]['title'], fontsize=10)
                        if not(onefig): legend(('Model','Data'))
                        xlabel(E[graph]['xlabel'])
                        ylabel(E[graph]['pops'][p]['ylabel'])
                        xlim(xmin=simstartyear, xmax=simendyear)
                        ylim(ymin=0)
                
                else: # Total epi graphs and cost graphs
                    if graph=='costann':
                        subkey = 'total' #['existing','future'][popstot]
                        xdata = E[graph][subkey]['total']['xdata'] 
                    elif graph in ['commit','costcum']:
                        subkey = 'total'
                        xdata = E[graph][subkey]['xdata'] 
                    else:
                        subkey = 'tot'
                        xdata = E['tvec']
                        
                    if onefig:
                        count += 1
                        subplot(nxplots, nyplots, count)
                    else:
                        figure(facecolor='w')
                    hold(True)
                    try:
                        if graph not in ['costann']:
                            fill_between(xdata, E[graph][subkey]['low'], E[graph][subkey]['high'], alpha=0.2, edgecolor='none')
                        else:
                            fill_between(xdata, E[graph][subkey]['total']['low'], E[graph][subkey]['total']['high'], alpha=0.2, edgecolor='none')
                    except:
                        import traceback; traceback.print_exc(); import pdb; pdb.set_trace()
                    if graph not in ['costann']:
                        plot(xdata, E[graph][subkey]['best'], c=E['colorm'], linewidth=linewidth)
                    else:
                        plot(xdata, E[graph][subkey]['total']['best'], c=E['colorm'], linewidth=linewidth)
                    if epigraph:
                        if ndim(E[graph]['ydata'])==1:
                            scatter(E['xdata'], E[graph]['ydata'], c=E['colord'])
                    
                    if graph not in ['costann']:
                        title(E[graph][subkey]['title'], fontsize=10)
                    else:
                        title(E[graph][subkey]['total']['title'], fontsize=10)
                    if epigraph: xlabel(E[graph]['xlabel'])
                    else: 
                        if graph not in ['costann']:
                            xlabel(E[graph][subkey]['xlabel'])
                            ylabel(E[graph][subkey]['ylabel'])
                        else:
                            xlabel(E[graph][subkey]['total']['xlabel'])
                            ylabel(E[graph][subkey]['total']['ylabel'])
                    
                    ylim(ymin=0)
    
    if onefig:
        subplot(nxplots, nyplots, count+1)
        plot(1, 1, c=E['colorm'], linewidth=linewidth, label='Model')
        fill_between([1,2], [1,1], [2,2], alpha=0.2, edgecolor='none', label='Uncertainty')
        scatter(0, 0, c=E['colord'], label='Data')
        xlim((0,1))
        ylim((0,1))
        legend()
        
    if show_wait: show()



def viewmultiresults(M, whichgraphs={'prev':[1,1], 'plhiv':[0,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1], 'costcum':[1,1]}, simstartyear=2000, simendyear=2030, onefig=True, verbose=2, show_wait=False, linewidth=2):
    """
    Generate all outputs required for the model, including prevalence, incidence,
    deaths, etc.
    Version: 2015mar23
    """
    
    from matplotlib.pylab import figure, plot, hold, xlabel, ylabel, xlim, ylim, legend, title, ceil, sqrt, subplot, show, fill_between
    import brewer2mpl as colormap
    bmap = colormap.get_map('Paired', 'Qualitative', max(3,M['nsims'])) # WARNING, won't work with >13
    if M['nsims']>12: raise Exception('Can''t use ColorBrewer with more than 12 colors')
    colors = bmap.mpl_colors
    
    npops = len(M.prev['pops']) # Calculate number of populations

    
    if onefig:
        figh = figure(figsize=(24,16), facecolor='w')
        figh.subplots_adjust(left=0.04) # Less space on left
        figh.subplots_adjust(right=0.99) # Less space on right
        figh.subplots_adjust(top=0.98) # Less space on bottom
        figh.subplots_adjust(bottom=0.04) # Less space on bottom
        figh.subplots_adjust(wspace=0.5) # More space between
        figh.subplots_adjust(hspace=0.5) # More space between
        nplots = onefig
        for graph in whichgraphs.keys():
            for i in range(len(whichgraphs[graph])):
                if graph[0:4] != 'cost': nplots += whichgraphs[graph][i]*[npops,1][i]
                else: nplots += whichgraphs[graph][i]
        nxplots = ceil(sqrt(nplots))
        nyplots = nxplots
        while nxplots*nyplots>nplots: nyplots -= 1
        if nxplots*nyplots<nplots: nyplots += 1
    
    count = 0
    for graph in whichgraphs.keys(): # Loop over each type of data, e.g. prevalence
        epigraph = (graph[0:4] != 'cost') # Flag for whether or not it's an epi graph vs. a cost graph
        for popstot in range(2): # Loop over population or total graphs
            if whichgraphs[graph][popstot]:
                if popstot==0 and epigraph: # Population graphs for epi data
                    for p in range(npops):
                        if onefig:
                            count += 1
                            subplot(nxplots, nyplots, count)
                        else:
                            figure(facecolor='w')
                        hold(True)
                        for sim in range(M['nsims']):
                            if graph not in ['costann']:
                                fill_between(M['tvec'], M[graph]['pops'][p]['low'][sim], M[graph]['pops'][p]['high'][sim], alpha=0.2, edgecolor='none')
                            plot(M['tvec'], M[graph]['pops'][p]['best'][sim], linewidth=linewidth, color=colors[sim])
                        
                        title(M[graph]['pops'][p]['title'], fontsize=10)
                        if not(onefig): legend(M[graph]['pops'][p]['legend'])
                        xlabel(M[graph]['xlabel'])
                        ylabel(M[graph]['pops'][p]['ylabel'])
                        xlim(xmin=simstartyear, xmax=simendyear)
                        ylim(ymin=0)
                
                else: # Total epi graphs and cost graphs
                    if epigraph:
                        subkey = 'tot'
                        xdata = M['tvec']
                    else:
                        subkey = 'total' #['existing','future'][popstot] # SUPER CONFUSING
                        xdata = M[graph][subkey]['xdata']
                    
                    if onefig:
                        count += 1
                        subplot(nxplots, nyplots, count)
                    else:
                        figure(facecolor='w')
                    hold(True)
                    
                    for sim in range(M['nsims']):
                        plot(xdata, M[graph][subkey]['data'][sim], linewidth=linewidth, color=colors[sim])
                    
                    title(M[graph][subkey]['title'], fontsize=10)
                    if epigraph: xlabel(M[graph]['xlabel'])
                    else: xlabel(M[graph][subkey]['xlabel'])
                    ylabel(M[graph][subkey]['ylabel'])
                    ylim(ymin=0)
    
    if onefig:
        subplot(nxplots, nyplots, count+1)
        for sim in range(M['nsims']): plot(0, 0, linewidth=linewidth, color=colors[sim])
        legend(M[graph]['total']['legend'])

    if show_wait: show()



def viewoptimresults(O):
    """
    Plot pies and outcome
    Version: 2015mar25
    """
    from matplotlib.pylab import figure, subplot, pie, title, plot, xlabel, ylabel
    import brewer2mpl as colormap
    
    nprograms = len(O['alloc'][0]['piedata'])
    bmap = colormap.get_map('Paired', 'Qualitative', max(3,nprograms)) # WARNING, won't work with >13
    if nprograms>12: raise Exception('Can''t use ColorBrewer with more than 12 colors')
    colors = bmap.mpl_colors
    
    figure(figsize=(8,8))
    for p in range(2):
        subplot(2,2,p+1)
        pie(O['alloc'][p]['piedata'], colors=colors, labels=O['alloc'][p]['legend'])
        title(O['alloc'][p]['title'])
    subplot(2,1,2)
    plot(O['outcome']['xdata'], O['outcome']['ydata'])
    xlabel(O['outcome']['xlabel'])
    ylabel(O['outcome']['ylabel'])
    title(O['outcome']['title'])