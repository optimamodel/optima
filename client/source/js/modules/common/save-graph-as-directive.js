define(['angular', 'underscore', 'saveAs'], function (angular, _, saveAs) {
  'use strict';

  return angular.module('app.save-graph-as', [])
    .directive('saveGraphAs', function ($http, modalService) {
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

          var exportGraphAsSVG = function() {
            var svgContent = elem.parent().find('svg').html();

            // in order to have styled graphs the css content used to render
            // graphs is retrieved & inject it into the svg as style tag
            var cssContentRequest = $http.get('/assets/css/chart.css');
            cssContentRequest.success(function(cssContent) {
              var styles = '<style>' + cssContent + '</style>';
              var svgGraph = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">';
              svgGraph = svgGraph + styles;
              svgGraph = svgGraph + svgContent;
              svgGraph = svgGraph + '</svg>';

              saveAs(new Blob([svgGraph], { type: 'image/svg' }), 'graph.svg');
            }).error(function() {
              alert("Please releod and try again, something went wrong while generating the graph.");
            });
          };

          var exportGraphAsPNG = function() {
            var svgElement = elem.parent().find('svg');
            var svgContent = svgElement.html();

            var scalingFactor = 4.2;

            // in order to have styled graphs the css content used to render
            // graphs is retrieved & inject it into the svg as style tag
            var cssContentRequest = $http.get('/assets/css/chart.css');
            cssContentRequest.success(function(cssContent) {
              var styles = '<style>' + cssContent + '</style>';

              var viewbox = ' viewbox="0 0 ' + svgElement.width() + ' ' + svgElement.height() + '"';
              var svgAttributes = ' xmlns="http://www.w3.org/2000/svg"';
              svgAttributes = svgAttributes + ' width="' + svgElement.width() + '"';
              svgAttributes = svgAttributes + ' height="' + svgElement.height() + '"';
              svgAttributes = svgAttributes + viewbox;

              var svgGraph = '<svg' + svgAttributes + '>';
              svgGraph = svgGraph + styles;
              svgGraph = svgGraph + svgContent;
              svgGraph = svgGraph + '</svg>';

              var tmpImage = document.createElement("img");
              tmpImage.width = svgElement.width() * scalingFactor;
              tmpImage.height = svgElement.height() * scalingFactor;
              tmpImage.setAttribute("src", "data:image/svg+xml;base64," + btoa(svgGraph));

              tmpImage.onload = function() {
                var canvas = document.createElement("canvas");
                canvas.width = svgElement.width() * scalingFactor;
                canvas.height = svgElement.height() * scalingFactor;
                var ctx = canvas.getContext("2d");
                ctx.drawImage(tmpImage, 0, 0);

                canvas.toBlob(function(blob) {
                  saveAs(blob, "pretty image.png");
                });
              };
            }).error(function() {
              alert("Please releod and try again, something went wrong while generating the graph.");
            });
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
            xOfPoints.title = graph.options.xAxis.axisLabel;
            xOfPoints.data = [];
            xOfPoints.data.push.apply(xOfPoints.data, Object.keys(line));
            xOfPoints.data.push.apply(xOfPoints.data, Object.keys(scatter));
            xOfPoints.data.sort();
            exportable.columns.push(xOfPoints);

            var yOfPoints = {};
            yOfPoints.title = 'line'; // in theory, yAxis should be overall y title (todo for later, backend should support that)
            yOfPoints.data = fillFromDictionary(xOfPoints.data, line);
            exportable.columns.push(yOfPoints);

            _(graph.data.area).each(function(lineData, lineTitle) {
              var nextLine = graphToDictionary(lineData);
              var yOfPoints = {};
              yOfPoints.title = lineTitle;
              yOfPoints.data = fillFromDictionary(xOfPoints.data, nextLine);
              exportable.columns.push(yOfPoints);
            });

            var scatterPoints = {};
            scatterPoints.title = "scatter";
            scatterPoints.data = fillFromDictionary(xOfPoints.data, scatter);
            exportable.columns.push(scatterPoints);
            return exportable;
          };

          scope.linesExport = function (graph){
            var exportable = {
              name: graph.title,
              columns: []
            };

            var lineTitles = graph.legend? graph.legend : ["line", "high", "low"];

            // The X of the points are only sent in one column and we collect them from any of the lines
            var xOfPoints = {};
            xOfPoints.title = graph.options.xAxis.axisLabel;
            xOfPoints.data = _.map(graph.data.lines[0],function(point,j){ return point[0]; });
            exportable.columns.push(xOfPoints);

            _(graph.data.lines).each(function(lineData, index) {
              // Collecting the Y of the points for the line
              var yOfLinePoints = {};
              yOfLinePoints.title = lineTitles[index];
              yOfLinePoints.data = _.map(lineData,function(point,j){ return point[1]; });
              exportable.columns.push(yOfLinePoints);
            });

            return exportable;
          };

          /**
           * Returns the normalized data ready for export
           */
          scope.getExportableFrom = function (graph){
            if(!graph.data) { return null; }
            if(_.isEqual(Object.keys(graph.data),["line", "scatter", "area"])) { return scope.lineAndAreaExport(graph); }
            if(_.isEqual(Object.keys(graph.data),["lines", "scatter"])) { return scope.linesExport(graph); }

            return null;
          };

          scope.saySorry = function() {
            // to-do: this should be updated after the PR to use the modalService
            return alert('Sorry, this graph cannot be exported');
          };

          /**
           * Exports the data of the graph in the format returned by the API
           */
          scope.exportFrom = function (graphOrUndefined){
            if(!graphOrUndefined) { return scope.saySorry();}
            var exportable = this.getExportableFrom(graphOrUndefined);
            if(exportable === null) { return scope.saySorry(); }

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
            .on('click', '.figure', function (event) {
              event.preventDefault();

              var message = 'Please choose your preferred format';
              modalService.choice(
                exportGraphAsSVG,
                exportGraphAsPNG,
                'Download as SVG',
                'Download as PNG',
                message,
                'Export figure'
              );
            })
            .on('click', '.data', function (event) {
              event.preventDefault();
              //a big ugly hack to distinguish between cost and covariance graphs.
              //they are both in the same ng-repeat scope :-(
              var target = attrs.variant == 'coGraph'? scope.coGraph: scope.graph;
              scope.exportFrom(target);
            });
        }
      };
    });

});
