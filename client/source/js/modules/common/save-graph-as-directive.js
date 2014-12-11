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
            var low, line, high;
            var exportable = {
              name: graph.title,
              columns: []
            };

            low = graph.data.lines[2];
            line = graph.data.lines[0];
            high = graph.data.lines[1];

            // The X of the points are only sent in one column and we collect them from any of the lines
            var xOfPoints = {};
            xOfPoints['title'] = graph.options.xAxis.axisLabel;
            xOfPoints['data'] = _.map(line,function(point,j){ return point[0] });
            exportable.columns.push(xOfPoints);

            // Collecting the Y of the points for the line
            var yOfLinePoints = {};
            yOfLinePoints['title'] = 'line';
            yOfLinePoints['data'] = _.map(line,function(point,j){ return point[1] });
            exportable.columns.push(yOfLinePoints);

            // Collecting the Y of the points for the lower boundary
            var yOfLowPoints = {};
            yOfLowPoints['title']='low';
            yOfLowPoints['data'] =_.map(low,function(point,j){ return point[1] }); // collects all the y values of the points
            exportable.columns.push(yOfLowPoints);

            // Collecting the Y of the points for the higher boundary
            var yOfHighPoints = {};
            yOfHighPoints['title']='high';
            yOfHighPoints['data'] =_.map(high,function(point,j){ return point[1] }); // collects all the y values of the points
            exportable.columns.push(yOfHighPoints);

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
                var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                saveAs(blob, (graphOrUndefined.title+'.xlsx'));
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
            });
        }
      };
    });

});
