define(['angular', 'saveAs'], function (angular, saveAs) {
  'use strict';

  return angular.module('app.save-graph-as', [])
    .directive('saveGraphAs', function ($http) {
      return {
        restrict: 'A',
        link: function (scope, elem, attrs) {
          var html = '<div class="chart-buttons btn-group">' +
            '<button class="btn figure">Export figure</button>' +
            '<button class="btn data">Export data</button>' +
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
            .on('click', '.data', function (e) {
              console.log("!!!")
              e.preventDefault();
              var data = {
                name: 'my_table',
                columns: [
                  { data: [1, 2, 3], title: 'x axis' },
                  { data: [1, 2, 3], title: 'y axis' }
                ]
              };
              $http({url:'/api/project/export', 
                    method:'POST', data:data, 
                    headers: {'Content-type': 'application/json'},
                    responseType:'arraybuffer'})
                .success(function (response, status, headers, config) {
                  console.log(status, headers, config);
                  var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                  saveAs(blob, 'my_table.xlsx');
                })
                .error(function () {});
            });
        }
      };
    });

});
