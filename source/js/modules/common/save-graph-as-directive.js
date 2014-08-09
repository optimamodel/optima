define(['angular', 'saveAs'], function (angular, saveAs) {
  'use strict';

  return angular.module('app.save-graph-as', [])
    .directive('saveGraphAs', function () {
      return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
          var html = '<div class="chart-buttons btn-group">' +
            '<button class="btn svg">Save as SVG</button>' +
            '<button class="btn pdf">Save as PDF</button>' +
            '<button class="btn png">Save as PNG</button>' +
            '<div id="svgdataurl" style="display: none"></div>' +
            '<div id="pngdataurl" style="display: none"></div>' +
            '</div>';

          var buttons = angular.element(html);

          elem.after(buttons);

          buttons
            .on('click', '.svg', function (e) {
              e.preventDefault();

              var xml = elem.find('svg')
                .attr({
                  'xmlns': 'http://www.w3.org/2000/svg',
                  'version': 1.1
                })
                .parent().html();

              saveAs(new Blob([xml], { type: 'image/svg' }), 'graph.svg');
            })
            .on('click', '.pdf, .png', function (e) {
              e.preventDefault();
              alert('Thanks for clicking, but this feature is currently under development');
            });
        }
      };
    });

});
