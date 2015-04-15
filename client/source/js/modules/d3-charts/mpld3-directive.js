define(['./module','underscore', 'jquery', 'mpld3'], function (module, _, $) {
  'use strict';

  module.directive('mpld3Chart', function () {

    return {
      scope: {
        chart: '='
      },
      link: function (scope, element) {
        var newId = 'mpld3-chart' + _.uniqueId();
        $(element).attr('id', newId);
//        mpld3.draw_figure(newId, scope.props);
        scope.$watch('chart', function() { // before this change, all the graphs were redrawn three times
          console.log("calling mpld3 for element", element, scope.chart);
          $(element).html("");
          mpld3.draw_figure(newId, scope.chart);
        }, true);
      }
    };
  });
});
