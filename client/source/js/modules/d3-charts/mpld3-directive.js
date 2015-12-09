define(['./module','underscore', 'jquery', 'mpld3'], function (module, _, $, mpld3) {
  'use strict';

  module.directive('mpld3Chart', function () {
    return {
      scope: {
        chart: '=mpld3Chart'
      },
      link: function (scope, element, attrs) {
        $(element).attr('class', 'mpld3-chart');
        scope.$watch('chart', function() {
          $(element).html("");
          mpld3.draw_figure(attrs.id, scope.chart);
        }, true);
      }
    };
  });
});
