def gridcolormap(npts=10, limits=None, nsteps=10, doplot=False, asarray=False):
    """
    GRIDCOLORMAP

    Create a qualitative colormap by assigning points according to the minimum pairwise distance.

    Usage example:
    from matplotlib.pylab import *
    from gridcolormap import gridcolormap
    ncolors = 10
    piedata = rand(ncolors)
    colors = gridcolormap(ncolors, doplot=True)
    figure()
    pie(piedata, colors=colors)
    show()

    Version: 1.0 (2015may13) by cliffk
    """

    ## Imports
    from numpy import linspace, meshgrid, array, transpose, inf, zeros, argmax, minimum
    from numpy.linalg import norm
    
    ## Calculate sliding limits if none provided
    if limits is None:
        colorrange = 1-1/float(npts**0.5)
        limits = [0.5-colorrange/2, 0.5+colorrange/2]
    
    ## Calculate primitives and dot locations
    primitive = linspace(limits[0], limits[1], nsteps) # Define primitive color vector
    x, y, z = meshgrid(primitive, primitive, primitive) # Create grid of all possible points
    dots = transpose(array([x.flatten(), y.flatten(), z.flatten()])) # Flatten into an array of dots
    ndots = nsteps**3 # Calculate the number of dots
    indices = [0] # Initialize the array
    
    ## Calculate the distances
    for pt in range(npts-1): # Loop over each point
        totaldistances = inf+zeros(ndots) # Initialize distances
        for ind in indices: # Loop over each existing point
            rgbdistances = dots - dots[ind] # Calculate the distance in RGB space
            totaldistances = minimum(totaldistances, norm(rgbdistances,axis=1)) # Calculate the minimum Euclidean distance
        maxindex = argmax(totaldistances) # Find the point that maximizes the minimum distance
        indices.append(maxindex) # Append this index
    
    ## Wrap up: optionally turn into a list of tuples
    if asarray:
        colors = []
        for i in indices: colors.append(tuple(dots[i,:])) # Gather output
    else:
        colors = dots[indices,:]
    
    ## For plotting
    if doplot:
        from mpl_toolkits.mplot3d import Axes3D # analysis:ignore
        from matplotlib.pyplot import figure
        fig = figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.cla()
        ax.scatter(dots[indices,0], dots[indices,1], dots[indices,2], c=colors, s=200, depthshade=False)
        ax.set_xlabel('R')
        ax.set_ylabel('G')
        ax.set_zlabel('B')
        ax.set_xlim((0,1))
        ax.set_ylim((0,1))
        ax.set_zlim((0,1))
        ax.grid(False)
    
    return colors
    
    


## Create colormap
def alpinecolormap(gap=0.1,mingreen=0.2,redbluemix=0.5,epsilon=0.01):
   """
   ALPINECOLORMAP

   This program generates a map based on ascending height. Based on data from
   Kazakhstan.

   Test case:
   import alpinecolormap
   alpinecolormap.testcolormap()

   Usage example:
   from alpinecolormap import alpinecolormap
   from pylab import randn, imshow, show
   imshow(randn(20,20),interpolation='none',cmap=alpinecolormap())
   show()

   Version: 2014aug06 by Cliff Kerr (cliff@thekerrlab.com)
   """
   from matplotlib.colors import LinearSegmentedColormap as makecolormap
   from pylab import array
   
   water = array([3,18,59])/256.
   desert = array([194,175,160*0.6])/256.
   forest1 = array([61,86,46])/256.
   forest2 = array([61,86,46])/256.*1.2
   rock = array([119,111,109])/256.*1.3
   snow = array([243,239,238])/256.
   breaks = [0.0,0.5,0.7,0.8,0.9,1.0]
   
   cdict = {'red': ((breaks[0], water[0], water[0]),
                    (breaks[1], desert[0], desert[0]),
                    (breaks[2], forest1[0], forest1[0]),
                    (breaks[3], forest2[0], forest2[0]),
                    (breaks[4], rock[0], rock[0]),
                    (breaks[5], snow[0], snow[0])),

         'green':  ((breaks[0], water[1], water[1]),
                    (breaks[1], desert[1], desert[1]),
                    (breaks[2], forest1[1], forest1[1]),
                    (breaks[3], forest2[1], forest2[1]),
                    (breaks[4], rock[1], rock[1]),
                    (breaks[5], snow[1], snow[1])),

         'blue':   ((breaks[0], water[2], water[2]),
                    (breaks[1], desert[2], desert[2]),
                    (breaks[2], forest1[2], forest1[2]),
                    (breaks[3], forest2[2], forest2[2]),
                    (breaks[4], rock[2], rock[2]),
                    (breaks[5], snow[2], snow[2]))}
   
   cmap = makecolormap('alpinecolormap',cdict,256)
   return cmap

## Show the staggering beauty of the color map's infinite possibilities
def testalpinecolormap():
    from pylab import randn, show, convolve, array, seed, linspace, meshgrid, xlabel, ylabel
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    
    maxheight = 3
    horizontalsize = 4;
    seed(8)
    n = 100
    smoothing = 40;
    kernel = array([0.25,0.5,0.25])
    data = randn(n,n)
    for s in range(smoothing): # Quick-and-dirty-and-slow smoothing
        for i in range(n): data[:,i] = convolve(data[:,i],kernel,mode='same')
        for i in range(n): data[i,:] = convolve(data[i,:],kernel,mode='same')
    data -= data.min()
    data /= data.max()
    data *= maxheight
    
    fig = plt.figure(figsize=(18,8))
    ax = fig.gca(projection='3d')
    ax.view_init(elev=45, azim=30)
    X = linspace(0,horizontalsize,n)
    X, Y = meshgrid(X, X)
    surf = ax.plot_surface(X, Y, data, rstride=1, cstride=1, cmap=alpinecolormap(), linewidth=0, antialiased=False)
    cb = fig.colorbar(surf)
    cb.set_label('Height (km)',horizontalalignment='right', labelpad=50)
    xlabel('Position (km)')
    ylabel('Position (km)')
    show()

    fig = plt.figure(figsize=(8,6))
    ax = fig.gca()
    X = linspace(0,horizontalsize,n)
    pcl = plt.pcolor(X, X, data, cmap=alpinecolormap(), linewidth=0, antialiased=False)
    cb2 = fig.colorbar(pcl)
    cb2.set_label('Height (km)',horizontalalignment='right', labelpad=50)
    xlabel('Position (km)')
    ylabel('Position (km)')
    show()





def vectocolor(vector,cmap=None):
   """
   VECTOCOLOR
   This function converts a vector of N values into an Nx3 matrix of color
   values according to the current colormap. It automatically scales the 
   vector to provide maximum dynamic range for the color map.

   Usage:
   colors=vectocolor(vector,cmap=None)

   where:
   colors is an Nx4 list of RGB-alpha color values
   vector is the input vector (or list, it's converted to an array)
   cmap is the colormap (default: jet)

   Example:
   n=1000
   x=randn(n,1);
   y=randn(n,1);
   c=vectocolor(y);
   scatter(x,y,20,c)

   Version: 1.0 (2012sep13 by cliffk)
   """
   from pylab import array, zeros

   if cmap==None:
      from pylab import cm
      cmap=cm.jet;

   # The vector has elements
   if len(vector):
      vector = array(vector) # Just to be sure
      vector = vector-vector.min() # Subtract minimum
      vector = vector/float(vector.max()) # Divide by maximum
      nelements = len(vector) # Count number of elements
      colors=zeros((nelements,4))
      for i in range(nelements):
         colors[i,:]=array(cmap(vector[i]))

   # It doesn't; just return black
   else: colors=(0,0,0,1)

   return colors






## Create colormap
def bicolormap(gap=0.1,mingreen=0.2,redbluemix=0.5,epsilon=0.01):
   """
   BICOLORMAP

   This program generators a two-color map, blue for negative, red for
   positive changes, with grey in the middle. The input argument is how much
   of a color gap there is between the red scale and the blue one.

   The function has four parameters:
     gap: sets how big of a gap between red and blue color scales there is (0=no gap; 1=pure red and pure blue)
     mingreen: how much green to include at the extremes of the red-blue color scale
     redbluemix: how much red to mix with the blue and vice versa at the extremes of the scale
     epsilon: what fraction of the colormap to make gray in the middle

   Examples:
     bicolormap(gap=0,mingreen=0,redbluemix=1,epsilon=0) # From pure red to pure blue with white in the middle
     bicolormap(gap=0,mingreen=0,redbluemix=0,epsilon=0.1) # Red -> yellow -> gray -> turquoise -> blue
     bicolormap(gap=0.3,mingreen=0.2,redbluemix=0,epsilon=0.01) # Red and blue with a sharp distinction between

   Version: 1.0 (2013sep13 by cliffk)
   """
   from matplotlib.colors import LinearSegmentedColormap as makecolormap
   
   mng=mingreen; # Minimum amount of green to add into the colors
   mix=redbluemix; # How much red to mix with the blue an vice versa
   eps=epsilon; # How much of the center of the colormap to make gray
   omg=1-gap # omg = one minus gap
   
   cdict = {'red': ((0.00000, 0.0, 0.0),
                    (0.5-eps, mix, omg),
                    (0.50000, omg, omg),
                    (0.5+eps, omg, 1.0),
                    (1.00000, 1.0, 1.0)),

         'green':  ((0.00000, mng, mng),
                    (0.5-eps, omg, omg),
                    (0.50000, omg, omg),
                    (0.5+eps, omg, omg),
                    (1.00000, mng, mng)),

         'blue':   ((0.00000, 1.0, 1.0),
                    (0.5-eps, 1.0, omg),
                    (0.50000, omg, omg),
                    (0.5+eps, omg, mix),
                    (1.00000, 0.0, 0.0))}
   cmap = makecolormap('bicolormap',cdict,256)

   return cmap

## Show the staggering beauty of the color map's infinite possibilities
def testbicolormap():
    from pylab import figure, subplot, imshow, colorbar, rand, show
    
    maps=[]
    maps.append(bicolormap()) # Default ,should work for most things
    maps.append(bicolormap(gap=0,mingreen=0,redbluemix=1,epsilon=0)) # From pure red to pure blue with white in the middle
    maps.append(bicolormap(gap=0,mingreen=0,redbluemix=0,epsilon=0.1)) # Red -> yellow -> gray -> turquoise -> blue
    maps.append(bicolormap(gap=0.3,mingreen=0.2,redbluemix=0,epsilon=0.01)) # Red and blue with a sharp distinction between
    nexamples=len(maps)
    
    figure(figsize=(5*nexamples,4))    
    for m in range(nexamples):
        subplot(1,nexamples,m+1)
        imshow(rand(20,20),cmap=maps[m],interpolation='none');
        colorbar()
    show()