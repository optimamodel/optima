"""
OPTIMIZE
Run optimization. The data structure "objectives" is from the "Optimize outcomes" screen of http://54.200.79.218/#/optimization/objectives.
Version: 2014oct29
"""

def optimize(projectname='example', maxtime=60, objectives={}):
    from matplotlib.pylab import rand, r_, exp # KLUDGY
    from bunch import Bunch as struct # Replicate Matlab-like structure behavior

    
    # Generate data for scatter and line plots
    nplots = 2 # Original and optimal
    lineplotdata = []
    for p in range(nplots):
        lineplotdata.append(struct())
        lineplotdata[p].xmodeldata = r_[2000:2015] # Model output
        lineplotdata[p].ymodeldata = exp(-rand(len(lineplotdata[p].xmodeldata)))
        lineplotdata[p].xlabel = 'Year'
        lineplotdata[p].ylabel = 'Prevalence'
    
    pieplotdata = []
    for p in range(nplots):
        pieplotdata.append(struct())
        pieplotdata[p].piedata = [0.35, 0.12, 0.34, 0.28] # Experimental data
        pieplotdata[p].title = 'Allocation'
        
    # e.g. 
#    from matplotlib.pylab import plot, hold, scatter, subplot

#    subplot(2,2,1)
#    plot(lineplotdata[p].xmodeldata, lineplotdata[p].ymodeldata)
#    subplot(3,2,p)
#    plot(lineplotdata[p].xmodeldata, lineplotdata[p].ymodeldata)
#    hold(True)
#    pie(pieplotdata[p].pie);
    
    return lineplotdata, pieplotdata
