define(['angular', 'underscore', 'saveAs'], function (angular, _, saveAs) {
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

          scope.lineAndAreaExport = function (graph){
            console.log('to be implemented');     
          };

          scope.linesExport = function (graph){
            var exportable = {
              name: 'exported',
              columns: []
            };
            _.each(graph.data.lines, function(line,i){
              var points = line;
              if (i==0) { // only for the first column
                var column_x = {};
                column_x['title']="x"; // starting simple, later we'll see how to get proper names here
                column_x['data'] = _.map(points,function(point,j){ return point[0] }); //ideally, we need x only once for the graph
                exportable.columns.push(column_x);
              }
              var column_y = {};
              column_y['title']=i+"_y";
              column_y['data'] =_.map(points,function(point,j){ return point[1] });
              exportable.columns.push(column_y);
              });      
            return exportable;
          };

          /**
           * Returns the normalized data ready for export
           */
          scope.getExportableFrom = function (graph){
            if(!graph.data) { return null }
            if(_.isEqual(Object.keys(graph.data),["line", "scatter", "area"])) { return scope.lineAndAreaExport(graph) }
            if(_.isEqual(Object.keys(graph.data),["lines", "scatter"])) { return scope.linesExport(graph) }

            // to-do: this should be updated after the PR to use the modalService
            alert('Sorry, we cannot export data from this source');
          };

          /**
           * Exports the data of the graph in the format returned by the API
           */
          scope.exportFrom = function (graphOrUndefined){
            if(!graphOrUndefined) { return alert('Sorry, this graph cannot be exported')}
            var exportable = this.getExportableFrom(graphOrUndefined);
            if(exportable == null) { return alert('Sorry, this graph cannot be exported')}
      
            $http({url:'/api/project/export', 
                  method:'POST', 
                  data: exportable, 
                  headers: {'Content-type': 'application/json'},
                  responseType:'arraybuffer'})
              .success(function (response, status, headers, config) {
//                console.log(status, headers, config);
                var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                saveAs(blob, 'my_table.xlsx');
              })
              .error(function () {});
          };

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
              e.preventDefault();
              scope.exportFrom(scope.graph);
              
              // var data = {
              //   name: 'my_table',
              //   columns: [
              //     { data: [1, 2, 3], title: 'x axis' },
              //     { data: [1, 2, 3], title: 'y axis' }
              //   ]
              // };

            });
        }
      };
    });

});
