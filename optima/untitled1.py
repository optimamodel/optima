"""
Version:
"""

from pylab import *; from optima import *
norig = 20; 
nnew = 500;  
smooth = ceil(nnew/norig/2.); 
xorig = array([0]+sorted(rand(norig-2).tolist())+[1])
xnew = linspace(0,1,nnew); 
y = rand(norig)
ynosmooth = smoothinterp(xnew, xorig, y, smoothness = 0)
ysmooth = smoothinterp(xnew, xorig, y, smoothness = smooth)
ypchip = pchip(xorig, y, xnew)
ypchipderiv = pchip(xorig, y, xnew, deriv=True)

subplot(2,1,1)
plot(xnew, ynosmooth)
plot(xnew, ysmooth)
plot(xnew, ypchip)

subplot(2,1,2)
plot(xnew[1:], diff(ynosmooth))
plot(xnew[1:], diff(ysmooth))
plot(xnew[1:], diff(ypchip))
plot(xnew, ypchipderiv)