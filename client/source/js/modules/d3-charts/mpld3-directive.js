define(['./module','underscore', 'jquery', 'mpld3'], function (module, _, $, mpld3) {
  'use strict';

  module.directive('mpld3Chart', function () {
    return {
      scope: {
        chart: '=mpld3Chart'
      },
      link: function (scope, element) {
        var newId = 'mpld3-chart' + _.uniqueId();
        $(element).attr('id', newId);
        $(element).attr('class', 'mpld3-chart');
        scope.$watch('chart', function() {
          $(element).html("");
          mpld3.draw_figure(newId, scope.chart);
        }, true);
      }
    };
  });
});
