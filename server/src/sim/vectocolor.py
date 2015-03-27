"""
VECTOCOLOR
This function converts a vector of N values into an Nx3 matrix of color
values according to the current colormap. It automatically scales the 
vector to provide maximum dynamic range for the color map.

Usage:
  colors = vectocolor(vector, cmap=None)

where:
  colors is an Nx4 list of RGB-alpha color values
  vector is the input vector (or list, it's converted to an array; or a scalar)
  cmap is the colormap (default: jet)

Example:
	n=1000
	x=randn(n,1);
	y=randn(n,1);
	c=vectocolor(y);
	scatter(x,y,20,c)

Version: 2014nov05 by cliffk
"""

def vectocolor(vector,cmap=None):
   from numpy import array, zeros

   if cmap==None:
      from matplotlib import cm
      cmap=cm.jet # TODO: use more awesome colormap
      
   if type(vector)==int:
      vector = range(vector) # They've netered a scalar, not a vector, so convert it to a vector
   
   # The vector has elements
   if len(vector):
       vector = array(vector) # Just to be sure
       vector = vector-vector.min() # Subtract minimum
       vector = vector/float(vector.max()) # Divide by maximum
       nelements = len(vector) # Count number of elements
       
       colors=zeros((nelements,4))
       for i in xrange(nelements):
          colors[i,:]=array(cmap(vector[i]))
    
   # It doesn't; just return black
   else: colors=(0,0,0,1)

   return colors
