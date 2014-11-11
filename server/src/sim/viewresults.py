def viewresults(D, whichgraphs={'prev':1, 'inci':1, 'daly':1, 'death':1, 'pops':1, 'tot':1}, startyear=2000, endyear=2015, verbose=2, onefig=False, show_wait=False):
    """
    Generate all outputs required for the model, including prevalence, incidence,
    deaths, etc.
    Version: 2014nov05
    """
    
    from matplotlib.pylab import figure, plot, hold, scatter, xlabel, ylabel, xlim, ylim, legend, title, ndim, ceil, sqrt, subplot, show
    
#    D.O = deepcopy(D.D.O) # Because otherwise it's a frickin' pointer

    if onefig:
        figh = figure(figsize=(24,16))
        figh.subplots_adjust(left=0.01) # Less space on left
        figh.subplots_adjust(right=0.99) # Less space on right
        figh.subplots_adjust(top=0.98) # Less space on bottom
        figh.subplots_adjust(bottom=0.02) # Less space on bottom
        figh.subplots_adjust(wspace=0.5) # More space between
        figh.subplots_adjust(hspace=0.5) # More space between
        nplots = (whichgraphs['tot'] + whichgraphs['pops']*D.G.npops) * (whichgraphs['prev'] + whichgraphs['inci'] + whichgraphs['daly'] + whichgraphs['death'])
        xyplots = ceil(sqrt(nplots))
    
    count = 0
    for graph in ['prev', 'inci', 'daly', 'death']:
        if whichgraphs[graph]:
            
            percent = 100 if graph=='prev' else 1 # Multiply by 100 if the graph is prevalence
            
            if whichgraphs['tot']:
                if onefig:
                    count += 1
                    subplot(xyplots, xyplots, count)
                else:
                    figure()
                hold(True)
                plot(D.O.tvec, D.O[graph].tot*percent, c=D.O.colorm)
                if ndim(D.O[graph].ydata)==1:
                    scatter(D.O.xdata, D.O[graph].ydata*percent, c=D.O.colord)
                
                xlabel(D.O[graph].xlabel)
                ylabel(D.O[graph].ylabel)
                xlim(xmin=startyear, xmax=endyear)
                ylim(ymin=0)
                
            if whichgraphs['pops']:
                for p in range(D.G.npops):
                    if onefig:
                        count += 1
                        subplot(xyplots, xyplots, count)
                    else:
                        figure()
                    hold(True)
                    plot(D.O.tvec, D.O[graph].pops[p,:]*percent, c=D.O.colorm)
                    if ndim(D.O[graph].ydata)==2:
                        scatter(D.O.xdata, D.O[graph].ydata[p,:]*percent, c=D.O.colord)
                    
                    title(D.O.poplabels[p])
                    legend(('Model','Data'))
                    xlabel(D.O[graph].xlabel)
                    ylabel(D.O[graph].ylabel)
                    xlim(xmin=startyear, xmax=endyear)
                    ylim(ymin=0)
    if show_wait:
        show()