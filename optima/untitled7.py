# -*- coding: utf-8 -*-
"""
Created on Wed Dec  2 18:31:43 2015

@author: cliffk
"""

from pylab import *

fig1 = figure()
ax1 = fig1.add_subplot(111)
pl1 = plot([3,4,7])

fig2 = figure()
ax2 = fig2.add_subplot(211)
#pl1 = plot([3,4,7])

properties = dir(ax1)

success = []
failure = []

for prop in properties:
    try:
        setattr(ax2, prop, getattr(ax1, prop))
        success.append(prop)
        print('Success: %s' % prop)
    except:
        try:
            ax2.set(prop, getattr(ax1, prop))
            success.append(prop)
            print('Success: %s' % prop)
        except:
            failure.append(prop)
            print('Failure: %s' % prop)


#    adjustable = box
#    agg_filter = None
#    alpha = None
#    anchor = C
#    animated = False
#    aspect = auto
#    autoscale_on = True
#    autoscalex_on = True
#    autoscaley_on = True
#    axes = Axes(0.125,0.1;0.352273x0.8)
#    axes_locator = None
#    axis_bgcolor = w
#    axisbelow = False
#    children = [<matplotlib.axis.XAxis object at 0x7f229a983210>,...
#    clip_box = None
#    clip_on = True
#    clip_path = None
#    contains = None
#    cursor_props = (1, (0.0, 0.0, 0.0, 1.0))
#    data_ratio = 1.0
#    default_bbox_extra_artists = [<matplotlib.axis.XAxis object at 0x7f229a983210>,...
#    figure = Figure(640x480)
#    frame_on = True
#    geometry = (1, 2, 1)
#    gid = None
#    images = <a list of 0 AxesImage objects>
#    label = 
#    legend = None
#    legend_handles_labels = ([], [])
#    lines = <a list of 0 Line2D objects>
#    navigate = True
#    navigate_mode = None
#    path_effects = []
#    picker = None
#    position = Bbox('array([[ 0.125     ,  0.1       ],\n       [...
#    rasterization_zorder = None
#    rasterized = None
#    renderer_cache = None
#    shared_x_axes = <matplotlib.cbook.Grouper object at 0x7f22aa59e8d0...
#    shared_y_axes = <matplotlib.cbook.Grouper object at 0x7f22aa59e950...
#    sketch_params = None
#    snap = None
#    subplotspec = <matplotlib.gridspec.SubplotSpec object at 0x7f229...
#    title = 
#    transform = IdentityTransform()
#    transformed_clip_path_and_affine = (None, None)
#    url = None
#    visible = True
#    window_extent = TransformedBbox(Bbox('array([[ 0.125     ,  0.1   ...
#    xaxis = XAxis(80.000000,48.000000)
#    xaxis_transform = BlendedGenericTransform(CompositeGenericTransform(...
#    xbound = (0.0, 1.0)
#    xgridlines = <a list of 6 Line2D xgridline objects>
#    xlabel = 
#    xlim = (0.0, 1.0)
#    xmajorticklabels = <a list of 6 Text xticklabel objects>
#    xminorticklabels = <a list of 0 Text xticklabel objects>
#    xscale = linear
#    xticklabels = <a list of 6 Text xticklabel objects>
#    xticklines = <a list of 12 Text xtickline objects>
#    xticks = [ 0.   0.2  0.4  0.6  0.8  1. ]
#    yaxis = YAxis(80.000000,48.000000)
#    yaxis_transform = BlendedGenericTransform(BboxTransformTo(Transforme...
#    ybound = (0.0, 1.0)
#    ygridlines = <a list of 6 Line2D ygridline objects>
#    ylabel = 
#    ylim = (0.0, 1.0)
#    ymajorticklabels = <a list of 6 Text yticklabel objects>
#    yminorticklabels = <a list of 0 Text yticklabel objects>
#    yscale = linear
#    yticklabels = <a list of 6 Text yticklabel objects>
#    yticklines = <a list of 12 Line2D ytickline objects>
#    yticks = [ 0.   0.2  0.4  0.6  0.8  1. ]
#    zorder = 0