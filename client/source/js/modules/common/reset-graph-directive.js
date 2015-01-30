define(['angular', 'jquery', 'underscore'],
  function (angular, $, _) {
  'use strict';

  return angular.module('app.reset-graph', [])
    .directive('resetGraph', function () {
      return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
          var chartCssUrl = '/assets/css/chart.css';

          /**
           * Initializes the directive by appending the html and setting up the
           * event handlers.
           */
          var initialize = function() {
            var template = '<div class="chart-left-buttons btn-group">' +
              '<button class="btn __green reset">Reset</button>' +
            '</div>';

            var buttons = angular.element(template);
            // append export buttons
            elem.after(buttons);

            // setup click handlers for the different actions
            buttons
              .on('click', '.reset', function (event) {
                event.preventDefault();
                resetGraph();
              });
          };

          var resetGraph = function () {
            var g = elem.parent().find('g.parent_group');
            g.attr("transform","translate(0,0) scale(1) ");
          };

          initialize();
        }
      };
    });

});
