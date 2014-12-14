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

          /**
           * Converts array of graph points to dictionary.
           */
          var graphToDictionary = function(graphPoints){
            var graphDict = {};
            _(graphPoints).each(function(point){
              graphDict[point[0]] = point[1];
            });
            return graphDict;
          };

          /**
           * Fills array according to reference dictionary keys, 
           * Copies values from source dictionary if key found there, otherwise creates empty entries
           */
          var fillFromDictionary = function(reference, source){
            var result = [];
            _(reference).each(function(key){
              var nextEntry = (key in source)? source[key] : ''; // source[key] || '' would not catch '0' entries
              result.push(nextEntry);
            });
            return result;
          };

          scope.lineAndAreaExport = function (graph){
            if (!graph.data || !graph.options) return null;

            var exportable = {
              name: graph.title,
              columns: []
            };

            var scatter = graphToDictionary(graph.data.scatter);
            var line = graphToDictionary(graph.data.line);

            var xOfPoints = {}; // merge xPoints with scatter x points
            xOfPoints['title'] = graph.options.xAxis.axisLabel;
            xOfPoints['data'] = [];
            xOfPoints['data'].push.apply(xOfPoints['data'], Object.keys(line));
            xOfPoints['data'].push.apply(xOfPoints['data'], Object.keys(scatter));
            xOfPoints['data'].sort();
            exportable.columns.push(xOfPoints);

            var yOfPoints = {};
            yOfPoints['title'] = 'line'; // in theory, yAxis should be overall y title (todo for later, backend should support that)
            yOfPoints['data'] = fillFromDictionary(xOfPoints['data'], line);
            exportable.columns.push(yOfPoints);

            _(graph.data.area).each(function(lineData, lineTitle) {
              var nextLine = graphToDictionary(lineData);
              var yOfPoints = {};
              yOfPoints['title'] = lineTitle;
              yOfPoints['data'] = fillFromDictionary(xOfPoints['data'], nextLine);
              exportable.columns.push(yOfPoints);
            });

            var scatterPoints = {};
            scatterPoints['title'] = "scatter";
            scatterPoints['data'] = fillFromDictionary(xOfPoints['data'], scatter);
            exportable.columns.push(scatterPoints);
            return exportable;
          };

          scope.linesExport = function (graph){
            var low, line, high;
            var exportable = {
              name: graph.title,
              columns: []
            };

            var lineTitles = graph.legend? graph.legend : ["line", "high", "low"];
            line = graph.data.lines[0];
            high = graph.data.lines[1];
            low = graph.data.lines[2];

            // The X of the points are only sent in one column and we collect them from any of the lines
            var xOfPoints = {};
            xOfPoints['title'] = graph.options.xAxis.axisLabel;
            xOfPoints['data'] = _.map(line,function(point,j){ return point[0] });
            exportable.columns.push(xOfPoints);

            _(graph.data.lines).each(function(lineData, index) {
              // Collecting the Y of the points for the line
              var yOfLinePoints = {};
              yOfLinePoints['title'] = lineTitles[index];
              yOfLinePoints['data'] = _.map(line,function(point,j){ return point[1] });
              exportable.columns.push(yOfLinePoints);
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

            return null;
          };

          scope.saySorry = function() {
            // to-do: this should be updated after the PR to use the modalService
            return alert('Sorry, this graph cannot be exported');
          }

          /**
           * Exports the data of the graph in the format returned by the API
           */
          scope.exportFrom = function (graphOrUndefined){
            if(!graphOrUndefined) { return scope.saySorry();}
            var exportable = this.getExportableFrom(graphOrUndefined);
            if(exportable == null) { return scope.saySorry();}
      
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
