define(['angular', 'saveAs'], function (angular, saveAs, modalService) {
  'use strict';

  return angular.module('app.save-graph-as', [])
    .directive('saveGraphAs', function () {
      return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
          var html = '<div class="chart-buttons btn-group">' +
            '<button class="btn figure">Export figure</button>' +
            '<button class="btn pdf">Export data</button>' + // Not sure why "btn pdf" works but "btn table" doesn't
            '<div id="svgdataurl" style="display: none"></div>' +
            '</div>';

          var buttons = angular.element(html);

          elem.after(buttons);

          buttons
            .on('click', '.figure', function (e) {
              e.preventDefault();

              var xml = elem.find('figure').html();

              xml = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">' + xml + '</svg>';

              saveAs(new Blob([xml], { type: 'image/svg' }), 'graph.svg');
            })
            .on('click', '.table', function (e) {
              e.preventDefault();

              var message = 'This feature is currently under development. We are working hard in make it happen for you!';
              modalService.inform(
                function (){ null }, 
                'Okay'
                message, 
                'Thanks for your interest!'
              );
            });
        }
      };
    });

});
