# local modules
from pylab import *
import matplotlib.pyplot as plt

figsize = (4,3)
fig1 = figure()
plot([3,4,7])
ax1 = fig1.axes[0]

fig2 = figure()
plot([15,23,7])
ax2 = fig2.axes[0]

fig3, (ax3, ax4) = plt.subplots(1,2)

fig3._axstack.remove( ax3)
fig3._axstack.remove( ax4)
ax1.set_subplotspec( ax3.get_subplotspec() )
ax2.set_subplotspec( ax4.get_subplotspec() )


#ax1.set_figure(fig3)
#ax2.set_figure(fig3)

ax1.set_axes_locator(ax3.get_axes_locator())


fig3._axstack.add(fig1._make_key(ax1), ax1)
fig3._axstack.add(fig2._make_key(ax2), ax2)
ax1.set_xscale('log')
ax2.set_xscale('log')
ax2.yaxis.set_ticks(())

# If possible (easy access to plotting data) use
# ax3.plot(x, y1)
# ax4.lpot(x, y2)


# Add legend
#for line3 in ax3.lines:
#    fig3.legend((line3,),
#                ('label 3',),
#                loc = 'upper center',
#                bbox_to_anchor = [0.5, -0.05])
# Make space for the legend beneath the subplots
plt.subplots_adjust(bottom = 0.2)
# Show only fig3
fig3.set_size_inches( fig1.get_size_inches() )
fig3.show()
#plot_defaults.savefig( fig_z07, small=False, figsize=figsize )
