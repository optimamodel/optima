"""
Version:
"""
from optima import odict, defaults, Par
from numpy import array, vstack, ceil

P = defaults.defaultproject()
parset = P.parsets[0]
ind = 0


#def plotpars(parset, ind=None):
if 1:
    if ind is None: ind = 0
    outstr = ''
    count = 0
    parstoplot = odict()
    pars = parset.pars[ind].values()
    simpars = parset.interp(inds=ind)[0]
    tvec = simpars['tvec']
    popkeys = simpars['popkeys']
    plotdata = array([['name','simpar','par_t', 'par_y']], dtype=object) # Set up array for holding plotting results
    for i in range(len(pars)):
        par = pars[i]
        if isinstance(par, Par):
            key1 = par.short
            if hasattr(par,'y'):# WARNING, add par.m as well?
                if hasattr(par.y, 'keys') and len(par.y.keys())>0: # Only ones that don't have a len are temp pars
                    nkeys = len(par.y.keys())
                    for k,key2 in enumerate(par.y.keys()):
                        if hasattr(par, 't'): t = par.t[key2]
                        else: t = tvec[0] # For a constant
                        count += 1
                        if nkeys==1: thissimpar = simpars[key1]
                        else: thissimpar = simpars[key1][k]
                        thisplot = array(['%3i. %s - %s' % (count-1, key1, key2), thissimpar, t, par.y[key2]], dtype=object)
                        if sum(thissimpar)==0: thisplot[0] += ' (zero)'
                        plotdata = vstack([plotdata, thisplot])
                else:
                    t = tvec[0] # For a constant
                    count += 1
                    thisplot = array(['%3i. %s' % (count-1, key1), simpars[key1], t, par.y], dtype=object)
                    plotdata = vstack([plotdata, thisplot])

plotdata = plotdata[1:,:] # Remove header
nplots = len(plotdata)
nrows = 5
ncols = 4
nperscreen = nrows*ncols
nscreens = ceil(nplots/float(nperscreen))



import matplotlib.pyplot as plt
from matplotlib.widgets import Button

# set up figure
fig = plt.figure()
plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.95, wspace=0.2, hspace=0.4)
axs = []
count = 0
for row in range(nrows):
    for col in range(ncols):
        count += 1
        axs.append(fig.add_subplot(nrows, ncols, count))

global position
position = 0
backframe = plt.axes([0.2, 0.03, 0.2, 0.03])
nextframe = plt.axes([0.6, 0.03, 0.2, 0.03])
backbut = Button(backframe, 'Back')
nextbut = Button(nextframe, 'Next')

def update():
    global position
    print(position)
    for i,ax in enumerate(axs):
        ax.cla()
        nplt = i+position
        if nplt<nplots:
            this = plotdata[nplt,:]
            print(this)
            ax.set_title(this[0])
            if   isinstance(this[1], (int, float)):   ax.plot(tvec, 0*tvec+this[1])
            elif len(this[1])==0:                     ax.set_title(this[0]+' is empty')
            elif len(this[1])==1:                     ax.plot(tvec, 0*tvec+this[1])
            elif len(this[1])==len(tvec):             ax.plot(tvec, this[1])
            else: print('Problem with "%s": "%s"' % (this[0], this[1]))
            try: ax.scatter(this[2],this[3])
            except Exception as E: print('Problem with "%s": "%s"' % (this[0], E.message))
            ax.set_ylim((0,1.1*ax.get_ylim()[1]))
            ax.set_xlim((tvec[0],tvec[-1]))
            

            
def updateback(event=None):
    global position
    position -= nperscreen
    position = max(0,position)
    print(position)
    update()

def updatenext(event=None):
    global position
    position += nperscreen
    position = min(nplots-nperscreen, position)
    print(position)
    update()


# call back function

#    frame = numpy.floor(sframe.val)
#    ln.set_xdata(xdata[frame])
#    ln.set_ydata((frame+1)* ydata[frame])
#    ax.set_title(frame)
#    ax.relim()
#    ax.autoscale_view()
    plt.draw()

# connect callback to slider
update()
backbut.on_clicked(updateback)
nextbut.on_clicked(updatenext)