def viewepiresults(O, whichgraphs={'prev':[1,1], 'inci':[0,1], 'daly':[0,1], 'death':[0,1], 'dx':[0,1], 'tx1':[0,1], 'tx2':[0,1]}, startyear=2000, endyear=2015, onefig=True, verbose=2, show_wait=False):
    """
    Generate all outputs required for the model, including prevalence, incidence,
    deaths, etc.
    Version: 2014nov23
    """
    
    from matplotlib.pylab import figure, plot, hold, scatter, xlabel, ylabel, xlim, ylim, legend, title, ndim, ceil, sqrt, subplot, show, fill_between
    
    npops = len(O.prev.pops) # Calculate number of populations
    
    if onefig:
        figh = figure(figsize=(24,16))
        figh.subplots_adjust(left=0.04) # Less space on left
        figh.subplots_adjust(right=0.99) # Less space on right
        figh.subplots_adjust(top=0.98) # Less space on bottom
        figh.subplots_adjust(bottom=0.04) # Less space on bottom
        figh.subplots_adjust(wspace=0.5) # More space between
        figh.subplots_adjust(hspace=0.5) # More space between
        nplots = sum([whichgraphs[key][i]*[npops,1][i] for i in range(2) for key in whichgraphs.keys()])
        xyplots = ceil(sqrt(nplots))
    
    count = 0
    for graph in whichgraphs.keys(): # Loop over each type of data, e.g. prevalence
        for popstot in range(2): # Loop over population or total graphs
            if whichgraphs[graph][popstot]:
                percent = 100 if graph=='prev' else 1 # Multiply by 100 if the graph is prevalence
                
                if popstot==0: # Population graphs
                    for p in range(npops):
                        if onefig:
                            count += 1
                            subplot(xyplots, xyplots, count)
                        else:
                            figure()
                        hold(True)
                        fill_between(O.tvec, O[graph].pops[p].low*percent, O[graph].pops[p].high*percent, alpha=0.2, edgecolor='none')
                        plot(O.tvec, O[graph].pops[p].best*percent, c=O.colorm)
                        if ndim(O[graph].ydata)==2:
                            scatter(O.xdata, O[graph].ydata[p,:]*percent, c=O.colord)
                        
                        title(O.poplabels[p])
                        legend(('Model','Data'))
                        xlabel(O[graph].xlabel)
                        ylabel(O[graph].ylabel)
                        xlim(xmin=startyear, xmax=endyear)
                        ylim(ymin=0)
                
                if popstot==1: # Total graphs
                    if onefig:
                        count += 1
                        subplot(xyplots, xyplots, count)
                    else:
                        figure()
                    hold(True)
                    fill_between(O.tvec, O[graph].tot.low*percent, O[graph].tot.high*percent, alpha=0.2, edgecolor='none')
                    plot(O.tvec, O[graph].tot.best*percent, c=O.colorm)
                    if ndim(O[graph].ydata)==1:
                        scatter(O.xdata, O[graph].ydata*percent, c=O.colord)
                    
                    title('Overall')
                    legend(('Model','Data'))
                    xlabel(O[graph].xlabel)
                    ylabel(O[graph].ylabel)
                    xlim(xmin=startyear, xmax=endyear)
                    ylim(ymin=0)

        if show_wait: show()




def viewallocpies(plotdata, show_wait=False):
    """ Little function to plot optimization pies """
    from matplotlib.pylab import figure, pie, legend, title, subplot, show
    
    figure(figsize=(12,4))
    
    subplot(1,3,1)
    pie(plotdata.pie1.val)
    title(plotdata.pie1.name)
    
    subplot(1,3,2)
    pie(plotdata.pie2.val)
    title(plotdata.pie2.name)
    
    legend(plotdata.legend, bbox_to_anchor=(2, 0.8))
    
    if show_wait: show()