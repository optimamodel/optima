define(['./module', 'underscore', 'jquery', 'mpld3'], function (module, _, $, mpld3) {

  'use strict';

  function val2str(val, limit, suffix) {
    var reducedVal = val / limit
    var nDecimal = reducedVal >= 1 ? 0 : 1;
    return reducedVal.toFixed(nDecimal) + suffix;
  }

  function reformatValStr(text) {
    var val = parseFloat(text);
    if (val >= 1E9) {
      text = val2str(val, 1E9, 'b')
    } else if (val >= 1E6) {
      text = val2str(val, 1E6, 'm')
    } else if (val >= 1E3) {
      text = val2str(val, 1E3, 'k')
    }
    return text;
  }

  function reformatFigure($figure) {
    var $yaxis = $figure.find('.mpld3-yaxis');
    var $labels = $yaxis.find('g.tick > text');
    $labels.each(function () {
      var $label = $(this);
      var text = $label.text().replace(',', '');
      $label.text(reformatValStr(text));
    });

    $figure.find('svg.mpld3-figure').each(function () {
      var $svgFigure = $(this);

      // move mouse-over to bottom right corner
      $svgFigure.on('mouseover', function () {
        var height = parseInt($svgFigure.attr('height'));
        $svgFigure.find('.mpld3-coordinates').each(function () {
          $(this).attr('y', height + 7);
        });
        $svgFigure.find('.mpld3-toolbar').each(function () {
          $(this).remove();
        });
      });

      // add lines in legend labels
      var $axesLabels = $svgFigure.find('.mpld3-baseaxes > text');
      if ($axesLabels) {
        var nLegendLabels = $axesLabels.length - 2;
        var $paths = $svgFigure.find('.mpld3-axes > path');
        var $pathsToCopy = $paths.slice($paths.length - nLegendLabels, $paths.length);
        $svgFigure.find('.mpld3-baseaxes').append($pathsToCopy);
      }
    })
  }

  module.directive('mpld3Chart', function () {
    return {
      scope: {
        chart: '=mpld3Chart'
      },
      link: function (scope, element, attrs) {
        scope.$watch(
          'chart',
          function () {
            var $elem = $(element);
            $elem.attr('class', 'mpld3-chart');
            $elem.html("");

            var $$hashKey = scope.chart.$$hashKey;
            delete scope.chart.$$hashKey;
            mpld3.draw_figure(attrs.id, scope.chart);
            scope.chart.$$hashKey = $$hashKey;

            reformatFigure($elem);
          },
          true
        );
      }
    };
  });
});
