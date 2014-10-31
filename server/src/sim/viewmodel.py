"""
MAKETEMPLATE
http://54.200.79.218/#/model/view
it should return data for graphs
Version: 2014oct29
"""

def viewmodel(projectname='example', startyear=2000, endyear=2015):
    
    # Generate data for scatter and line plots
    nplots = 6
    plotdata = []
    for p in range(nplots):
        plotdata.append(struct())
        plotdata[p].xmodeldata = r_[2000:endyear+1] # Model output
        plotdata[p].ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
        plotdata[p].xexpdata = [2000, 2005, 2008] # Experimental data
        plotdata[p].yexpdata = [0.3, 0.4, 0.6]
        plotdata[p].xlabel = 'Year'
        plotdata[p].ylabel = 'Prevalence'
        
        # e.g. 
#        from matplotlib.pylab import plot, hold, scatter, subplot
#        subplot(3,2,p)
#        plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
#        hold(True)
#        scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
    
    return plotdata
