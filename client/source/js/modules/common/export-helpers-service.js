define(['angular', 'jquery', './svg-to-png'], function (angular, $, svgToPng) {
  'use strict';

  return angular.module('app.common.export-helpers',[])
  .factory('exportHelpers', ['$http', function ($http) {

    var chartCssUrl = '/assets/css/chart.css';

    var getCharts = function (scope) {
      var graphs = [];

      var controller = scope.exportCharts.controller;

      // Optimization
      if ( controller == 'AnalysisOptimization' ) {

        if ( scope.radarGraph ) {
          // export radarChart
          var graph = scope.radarGraph;
          graph.options.title = scope.radarGraphName;
          graphs.push(graph);
        }

        if ( scope.optimisationGraphs ) {
          graphs = graphs.concat(scope.optimisationGraphs);
        }

        if ( scope.financialGraphs ) {
          graphs = graphs.concat(scope.financialGraphs);
        }
      }

      // Calibration
      // Analysis Scenarios
      if ( controller == 'ModelCalibration' || controller == 'AnalysisScenarios' ) {
        if ( scope.graphs ) {
          graphs = scope.graphs;
        }
      }

      // Cost Coverage
      if ( controller == 'ModelCostCoverage' ) {
        if (scope.ccGraph) {
          graphs.push(scope.ccGraph);
        }

        if ( scope.graphs ) { // in this case, graphs are actually graph sets (one for cost, one for coverage)
          _(scope.graphs).each(function (graphSet,index) {
            _(graphSet).each(function (graph,index) {
              graphs.push(graph);
            });
          });
        }
      }
      return graphs;
    };

    /**
     * Get the graph as a PNG.
     *
     * In order to achieve this a new SVG is created including styles.
     * This SVG element is used as data source inside an image which then
     * is used to draw the content on a canvas to save it as PNG.
     */
    var generateGraphAsPngOrJpeg = function( el, callback, type ) {
      var originalSvg = el.find('svg');
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
        var style = originalStyle + '; background:#fff; ' + svgToPng.scalePaddingStyle(originalSvg, scalingFactor);

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

          // Return the png either as a blob or data url
          if ( type == 'blob' ) {
            canvas.toBlob( callback );
          } else {
            var data = canvas.toDataURL('image/jpeg', 1.0);
            callback( data );
          }
        };
      }).error(function() {
        alert("Please releod and try again, something went wrong while generating the graph.");
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

    var lineAndAreaExport = function (graph){
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

    var linesExport = function (graph){
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

    var areasExport = function (graph){
      var exportable = {
        name: graph.options.title || graph.title,
        columns: []
      };

      var areaTitles = graph.options.legend;

      // The X of the points are only sent in one column and we collect them from any of the lines
      var xOfPoints = {};
      xOfPoints.title = graph.options.xAxis.axisLabel;
      xOfPoints.data = _.map(graph.data.areas[0],function(point,j){ return point[0]; });
      exportable.columns.push(xOfPoints);

      _(graph.data.areas).each(function(areaData, index) {
        // Collecting the Y of the points for the area
        var yOfAreaPoints = {};
        yOfAreaPoints.title = areaTitles[index];
        yOfAreaPoints.data = _.map(areaData,function(point,j){ return point[1]; });
        exportable.columns.push(yOfAreaPoints);
      });

      return exportable;
    };

    /**
     * Returns the normalized data ready for export
     * for Radar Chart
     */
    var axesExport = function (graph){
      //x and y are not needed to be exported - they are just internal values to draw radar chart properly
      var exportable = {
        name: graph.radarGraphName,
        columns: []
      };

      var axisData = {};
      axisData.title = graph.radarAxesName;
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
    var getExportableFrom = function (graph){
      if(!graph.data) { return null; }
      if(_.isEqual(Object.keys(graph.data),["line", "scatter", "area"])) { return lineAndAreaExport(graph); }
      if(_.isEqual(Object.keys(graph.data),["lines", "scatter"])) { return linesExport(graph); }
      if(_.isEqual(Object.keys(graph.data),["areas"])) { return areasExport(graph); }
      if(_.isEqual(graph.data[0] && Object.keys(graph.data[0]),["axes"])) { return axesExport(graph); }

      return null;
    };

    var saySorry = function(msg) {
      // to-do: this should be updated after the PR to use the modalService
      if ( undefined !== msg ) {
        return alert(msg);
      } else {
        return alert('Sorry, this graph cannot be exported');
      }
    };

    return {
      generateGraphAsPngOrJpeg: generateGraphAsPngOrJpeg,
      getCharts: getCharts,
      saySorry: saySorry,
      getExportableFrom: getExportableFrom
    };
  }]);
});
