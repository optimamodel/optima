"""
OPTIMIZE
Run optimization. The data structure "objectives" is from the "Optimize outcomes" screen of http://54.200.79.218/#/optimization/objectives.
Version: 2014oct29
"""

def optimize(projectname='example', maxtime=60, objectives=[]):
   
     from dataio import loaddata, savedata
     D = loaddata(projectname+'.prj')
     from ballsd import ballsd
     ballsd(D.M, objectives) # Optimize parameters
    
     # Generate data for scatter and line plots
     lineplotdata.append(struct())
     lineplotdata.xmodeldata = r_[2000:2015] # Model output
     lineplotdata.ymodeldata = exp(-rand(len(plotdata[p].xmodeldata)))
     lineplotdata.xlabel = 'Year'
     lineplotdata.ylabel = 'Prevalence'
    
     nplots = 2 # Original and optimal
     pieplotdata = []
     for p in range(nplots):
        pieplotdata.append(struct())
        pieplotdata[p].piedata = [0.35, 0.12, 0.34, 0.28] # Experimental data
        pieplotdata[p].title = 'Allocation'
        
     # e.g. 
     from matplotlib.pylab import plot, hold, scatter, subplot
     
     subplot(2,2,1)
     plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
     subplot(3,2,p)
     plot(plotdata[p].xmodeldata, plotdata[p].ymodeldata)
     hold(True)
     scatter(plotdata[p].xexpdata, plotdata[p].yexpdata);
    
     return lineplotdata, pieplotdata
