def viewresults(D, whichgraphs={'prevpop':1, 'prevtot':1, 'incipop':1, 'prevtot':1, 'dalypop':1, 'dalytot':1, 'deathpop':1, 'deathtot':1}, startyear=2000, endyear=2015, verbose=2):
    """
    Generate all outputs required for the model, including prevalence, incidence,
    deaths, etc.
    Version: 2014nov05
    """
    
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
