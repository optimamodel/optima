"""
MANUALFIT
http://54.200.79.218/#/model/manual-calibration
Version: 2014oct28
"""

def manualfit(projectfilename='example.prj', tableparams):
    # Get input data from the editable table in the form of parameter name, parameter value, e.g. 'D.data.epi.p', 3.234
    
    # The project data file name needs to be 
    from matplotlib.pylab import rand, r_, exp # KLUDGY
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior
    
    # Generate data for scatter and line plots
    nplots = 6
    plotdata = []
    for p in range(nplots):
        plotdata.append(struct())
        plotdata[p].xmodeldata = r_[2000:2015] # Model output
        plotdata[p].ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
        plotdata[p].xexpdata = [2000, 2005, 2008] # Experimental data
        plotdata[p].yexpdata = [0.3, 0.4, 0.6]
        plotdata[p].xlabel = 'Year'
        plotdata[p].ylabel = 'Prevalence'
        
        # e.g. 
        from matplotlib.pylab import plot, hold, scatter, subplot
        subplot(3,2,p)
        plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
        hold(True)
        scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
    
    return plotdata
