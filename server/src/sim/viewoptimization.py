"""
VIEWOPTIMIZATION

Version: 2014oct28
"""

def viewoptimization(projectname='example', startyear=2000, endyear=2015):
    
    # Generate data for scatter and line plots
    nplots = 6
    lineplotdata = []
    
     nplots = 2 # Original and optimal
    pieplotdata = []
    for p in range(nplots):
        subplot(6,2,p)
        pieplotdata.append(struct())
        pieplotdata[p].piedata = [0.35, 0.12, 0.34, 0.28] # Experimental data
        pieplotdata[p].title = 'Allocation'
        
        
    for p in range(nplots):
        lineplotdata.append(struct())
        lineplotdata[p].xmodeldata = r_[2000:endyear+1] # Model output
        lineplotdata[p].ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
        lineplotdata[p].xexpdata = [2000, 2005, 2008] # Experimental data
        lineplotdata[p].yexpdata = [0.3, 0.4, 0.6]
        lineplotdata[p].xlabel = 'Year'
        lineplotdata[p].ylabel = 'Prevalence'
        
        # e.g. 
        from matplotlib.pylab import plot, hold, scatter, subplot
        subplot(6,2,p)
        plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
        hold(True)
        scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
        

    
    return plotdata
