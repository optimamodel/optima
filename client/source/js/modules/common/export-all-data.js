define(['underscore', './export-helpers-service'],
function (_) {
  'use strict';

  return angular.module('app.export-all-data', ['app.common.export-helpers'])
  .directive('exportAllData', function ($http, exportHelpers, modalService) {
    return {
      restrict: 'E',
      scope: {
        charts: '=',
        name: '@'
      },
      template: '<button type="button" class="btn" ng-click="exportAllData()">Export all data</button>',
      link: function (scope, elem, attrs) {

        /**
         * Exports the data of the graph in the format returned by the API
         */
        var exportMultiSheetFrom = function (graphs){
          if(graphs.length === 0) { modalService.inform(undefined,undefined, "Sorry, no graphs found"); }

          var exportables = [];
          var showAlert = false;
          _(graphs).each(function (graph, index) {

            // The only way to distinct the custom d3 charts from mpld3 charts is
            // to check for differences in the data structure. Checking for `id`
            // and `data` should be good enough.
            if (_(graph).has('id') && _(graph).has('data')) {
              var mpld3Exportable = exportHelpers.getMpld3ExportableFrom(graph);
              if ( mpld3Exportable ) {
                exportables.push(mpld3Exportable);
              } else {
                showAlert = true;
              }
            } else {
              var exportable = exportHelpers.getExportableFrom(graph);
              if ( exportable ) {
                exportables.push(exportable);
              } else {
                showAlert = true;
              }
            }
          });
          if(showAlert) { modalService.inform(undefined,undefined,"Sorry, some graphs cannot be exported"); }

          $http({url:'/api/project/exportall',
          method:'POST',
          data: exportables,
          headers: {'Content-type': 'application/json'},
          responseType:'arraybuffer'})
          .success(function (response, status, headers, config) {
            var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
            saveAs(blob, (scope.name + '.xlsx'));
          })
          .error(function () {});
        };

        /**
         * Export all graphs/charts data,
         */
        scope.exportAllData = function () {
          exportMultiSheetFrom(scope.charts);
        };
      }
    };
  });
});
