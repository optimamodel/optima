define(['./module','underscore', 'jquery', 'mpld3'], function (module, _, $, mpld3) {
  'use strict';


  function val2str(val, limit, suffix) {
   var reducedVal = val / limit
    var nDecimal = reducedVal >= 1 ? 0 : 1;
    return reducedVal.toFixed(nDecimal) + suffix;
  }


  function formatAxes(figure) {
    var axes = figure.find('.mpld3-yaxis');
    var ticks = axes.find('g.tick > text');
    ticks.each(function() {
      var text = $(this).text().replace(',', '')
      var val = parseFloat(text)
      if (val >= 1E9) {
          text = val2str(val, 1E9, 'b')
      } else if (val >= 1E6) {
          text = val2str(val, 1E6, 'm')
      } else if (val >= 1E3) {
          text = val2str(val, 1E3, 'k')
      }
      $(this).text(text);
    });
  }


  function set_overflow_visible() {
    var svgGraphFigures = $('svg.mpld3-figure');
    if (svgGraphFigures.length > 0 && !$(svgGraphFigures[0]).attr('data-pro2')) {
      svgGraphFigures.each(function() {
        $(this).css('overflow', 'visible');
        $(this).attr('data-pro2', true);
      });
    } else {
      setTimeout(set_overflow_visible, 150);
    }
  }

  function fix_mouse_pointer() {
    var svgGraphFigures = $('svg.mpld3-figure');
    if (svgGraphFigures.length > 0 && !$(svgGraphFigures[0]).attr('data-pro3')) {
      svgGraphFigures.each(function () {
        var that = this;
        $(that).on('mouseover', function() {
          $(that).find('.mpld3-coordinates').each(function () {
            $(this).attr('y', parseInt($(that).attr('height')) + 7);
          });
          $(that).find('.mpld3-toolbar').each(function () {
            $(this).remove();
          });
        });
        $(this).attr('data-pro3', true);
      });
    } else {
      setTimeout(fix_mouse_pointer, 150);
    }
  }

  function remove_default_plugin() {
    var svgGraphFigures = $('mpld3-toolbar');
    if (svgGraphFigures.length > 0 && !$(svgGraphFigures[0]).attr('data-pro4')) {
      svgGraphFigures.each(function () {
        $(this).remove();
        $(this).attr('data-pro4', true);
      });
    } else {
      setTimeout(remove_default_plugin, 150);
    }
  }

  module.directive('mpld3Chart', function () {
    return {
      scope: {
        chart: '=mpld3Chart'
      },
      link: function (scope, element, attrs) {
        $(element).attr('class', 'mpld3-chart');
        scope.$watch(
          'chart',
          function() {
            $(element).html("");
            mpld3.draw_figure(attrs.id, scope.chart);
            formatAxes($('#' + attrs.id))
          },
          true
        );
      }
    };
  });
});
