def viewresults(D, whichgraphs={'prev':1, 'inci':1, 'daly':1, 'death':1, 'pops':1, 'tot':1}, startyear=2000, endyear=2015, verbose=2):
    """
    Generate all outputs required for the model, including prevalence, incidence,
    deaths, etc.
    Version: 2014nov05
    """
    
    from matplotlib.pylab import figure, plot, hold, scatter, xlabel, ylabel, xlim, ylim, legend, title
    
    for graph in ['prev', 'inci', 'daly', 'death']:
        if whichgraphs[graph]:
            
            
            if whichgraphs['tot']:
                figure()
                plot(D.O.tvec, D.O[graph].tot)
                
                xlabel(D.O[graph].xlabel)
                ylabel(D.O[graph].ylabel)
                xlim(xmin=startyear, xmax=endyear)
                ylim(ymin=0)
                
            if whichgraphs['pops']:
                for p in range(D.G.npops):
                    figure()
                    hold(True)
                    plot(D.O.tvec, D.O[graph].pops[p,:], c=D.O.colorm)
                    scatter(D.O.xdata, D.O[graph].ydata[p,:], c=D.O.colord);
                    
                    title(D.O.poplabels[p])
                    legend(('Model','Data'))
                    xlabel(D.O[graph].xlabel)
                    ylabel(D.O[graph].ylabel)
                    xlim(xmin=startyear, xmax=endyear)
                    ylim(ymin=0)
            
        
    
    # Generate data for scatter and line plots
#    nplots = 6
#    plotdata = []
#    for p in range(nplots):
#        plotdata.append(struct())
#        plotdata[p].xmodeldata = r_[2000:endyear+1] # Model output
#        plotdata[p].ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
#        plotdata[p].xexpdata = [2000, 2005, 2008] # Experimental data
#        plotdata[p].yexpdata = [0.3, 0.4, 0.6]
#        plotdata[p].xlabel = 'Year'
#        plotdata[p].ylabel = 'Prevalence'
        
        # e.g. 
#        from matplotlib.pylab import plot, hold, scatter, subplot
#        subplot(3,2,p)
#        plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
#        hold(True)
#        scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
    
#    return plotdata
