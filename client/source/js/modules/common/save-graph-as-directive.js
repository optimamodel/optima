define(['angular', 'jquery', 'underscore', 'saveAs', './svg-to-png'],
  function (angular, $, _, saveAs, svgToPng) {
  'use strict';

  return angular.module('app.save-graph-as', [])
    .directive('saveGraphAs', function ($http, modalService) {
      return {
        restrict: 'A',
        link: function (scope, elem, attrs) {

          var chartCssUrl = '/assets/css/chart.css';

          /**
           * Initializes the directive by appending the html and setting up the
           * event handlers.
           */
          var initialize = function() {
            var template = '<div class="chart-buttons btn-group">' +
            '<button class="btn figure">Export figure</button>' +
            '<button class="btn data">Export data</button>' +
            '</div>';

            var buttons = angular.element(template);
            // append export buttons
            elem.after(buttons);

            // setup click handlers for the different actions
            buttons
              .on('click', '.figure', function (event) {
                event.preventDefault();

                modalService.choice(
                  exportGraphAsSvg, // first button callback
                  exportGraphAsPng, // second button callback
                  'Download as SVG', // first button text
                  'Download as PNG', // second button text
                  'Please choose your preferred format', // modal message
                  'Export figure' // modal title
                );
              })
              .on('click', '.data', function (event) {
                event.preventDefault();
                //a big ugly hack to distinguish between cost and covariance graphs.
                //they are both in the same ng-repeat scope :-(
                var target = {};
                if ( attrs.data == "radarData" ) {
                  target = {
                    data: scope.radarData,
                    options: scope.radarOptions
                  };
                  target.options.title = scope.radarChartName;

                } else if (attrs.variant == 'coGraph') {
                  target = scope.coGraph;
                } else if (attrs.variant == 'ccGraph') {
                  target = scope.ccGraph;
                } else {
                  target= scope.graph;
                }

                scope.exportFrom(target);
              });
          };

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

          /**
           * Initialize a download of the graph as SVG
           *
           * In this function the original SVG is enhanced by injecting styling.
           */
          var exportGraphAsSvg = function() {
            var originalSvg = elem.parent().find('svg');
            var orginalWidth = originalSvg.width();
            var orginalHeight = originalSvg.height();
            var originalStyle = originalSvg.attr('style');
            var scalingFactor = 1;

            // in order to have styled graphs the css content used to render
            // graphs is retrieved & inject it into the svg as style tag
            var cssContentRequest = $http.get(chartCssUrl);
            cssContentRequest.success(function(cssContent) {

              // create svg element
              var svg = svgToPng.createSvg(orginalWidth, orginalHeight, scalingFactor, originalStyle);

              // add styles and content to the svg
              var styles = '<style>' + cssContent + '</style>';
              svg.innerHTML = styles + originalSvg.html();

              // create img element with the svg as data source
              var svgXML = (new XMLSerializer()).serializeToString(svg);
              saveAs(new Blob([svgXML], { type: 'image/svg' }), 'graph.svg');
            }).error(function() {
              alert("Please reload and try again, something went wrong while generating the graph.");
            });
          };

          /**
           * Initializes a download of the graph as PNG
           *
           * In order to achieve this a new SVG is created including styles.
           * This SVG element is used as data source inside an image which then
           * is used to draw the content on a canvas to save it as PNG.
           */
          var exportGraphAsPng = function() {
            var originalSvg = elem.parent().find('svg');
            var orginalWidth = $(originalSvg).outerWidth();
            var orginalHeight = $(originalSvg).outerHeight();
            var originalStyle = originalSvg.attr('style');
            var scalingFactor = 4.2;

            // in order to have styled graphs the css content used to render
            // graphs is retrieved & inject it into the svg as style tag
            var cssContentRequest = $http.get(chartCssUrl);
            cssContentRequest.success(function(cssContent) {

              // make sure we scale the padding and append it to the original styling
              // info: later declarations overwrite previous ones
              var style = originalStyle + '; ' + svgToPng.scalePaddingStyle(originalSvg, scalingFactor);

              // create svg element
              var svg = svgToPng.createSvg(orginalWidth, orginalHeight, scalingFactor, style);

              // add styles and content to the svg
              var styles = '<style>' + cssContent + '</style>';
              svg.innerHTML = styles + originalSvg.html();

              // create img element with the svg as data source
              var svgXML = (new XMLSerializer()).serializeToString(svg);
              var tmpImage = document.createElement("img");
              tmpImage.width = orginalWidth * scalingFactor;
              tmpImage.height = orginalHeight * scalingFactor;
              tmpImage.src = "data:image/svg+xml;charset=utf-8,"+ svgXML;

              tmpImage.onload = function() {
                // draw image into canvas in order to convert it to a blob
                var canvas = document.createElement("canvas");
                canvas.width = orginalWidth * scalingFactor;
                canvas.height = orginalHeight * scalingFactor;
                var ctx = canvas.getContext("2d");
                ctx.drawImage(tmpImage, 0, 0);

                canvas.toBlob(function(blob) {
                  saveAs(blob, "graph.png");
                });
              };
            }).error(function() {
              alert("Please releod and try again, something went wrong while generating the graph.");
            });
          };

          scope.lineAndAreaExport = function (graph){
            if (!graph.data || !graph.options) return null;

            var exportable = {
              name: graph.options.title || graph.title,
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
              name: graph.options.title || graph.title,
              columns: []
            };

            var lineTitles = graph.options.legend? graph.options.legend : ["line", "high", "low"];

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
           * for Radar Chart
           */
          scope.axesExport = function (graph){
            //x and y are not needed to be exported - they are just internal values to draw radar chart properly
            var exportable = {
              name: scope.radarChartName,
              columns: []
            };

            var axisData = {}
            axisData.title = scope.radarAxesName;
            axisData.data = _.map(graph.data[0].axes, function(axis, j) { return axis.axis; });
            exportable.columns.push(axisData);

            _(graph.data).each(function(radarData, index) {
              var valueData = {};
              valueData.title = graph.options.legend[index];
              valueData.data = _.map(graph.data[index].axes, function(axis,j) { return axis.value; });
              exportable.columns.push(valueData);
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
            if(_.isEqual(graph.data[0] && Object.keys(graph.data[0]),["axes"])) { return scope.axesExport(graph); }

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
            var title = graphOrUndefined.options.title || graphOrUndefined.title;
            $http({url:'/api/project/export',
                  method:'POST',
                  data: exportable,
                  headers: {'Content-type': 'application/json'},
                  responseType:'arraybuffer'})
              .success(function (response, status, headers, config) {
                var blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                saveAs(blob, (title+'.xlsx'));
              })
              .error(function () {});
          };

          initialize();
        }
      };
    });

});
