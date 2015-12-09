define(['./scale-helpers', 'mpld3'], function (scaleHelpers, mpld3) {
  'use strict';

  function OptimaTickFormatter(fig, props) {
    mpld3.Plugin.call(this, fig, props);
  }

  mpld3.register_plugin("optimaTickFormatter", OptimaTickFormatter);
  OptimaTickFormatter.prototype = Object.create(mpld3.Plugin.prototype);
  OptimaTickFormatter.prototype.constructor = OptimaTickFormatter;
  OptimaTickFormatter.prototype.draw = function(){

    var xAxis = this.fig.axes[0].elements[0];
    var xLimits = this.fig.axes[0].props.xlim;
    var xFormat = scaleHelpers.evaluateTickFormat(xLimits[0], xLimits[1]);
    xAxis.axis.tickFormat(function (value) {
      return scaleHelpers.customTickFormat(value, xFormat);
    });

    var yAxis = this.fig.axes[0].elements[1];
    var yLimits = this.fig.axes[0].props.ylim;
    var yFormat = scaleHelpers.evaluateTickFormat(yLimits[0], yLimits[1]);
    yAxis.axis.tickFormat(function (value) {
      return scaleHelpers.customTickFormat(value, yFormat);
    });

    // Reset the figure to trigger a redraw. This is an unecessary overhead
    // but still better than patching mpld3 itself.
    this.fig.reset();
  };
});
