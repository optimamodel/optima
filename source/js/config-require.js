if (typeof define !== 'function') {
  // to be able to require file from node
  var define = require('amdefine')(module);
}

define({
  // Here paths are set relative to `/source/js` folder
  paths: {
    'angular'       : '../vendor/angular/angular',
    'async'         : '../vendor/requirejs-plugins/src/async',
    'canvg'         : '../vendor/canvg/dist/canvg.bundle',
    'canvas2blob'   : '../vendor/canvas-toBlob.js/canvas-toBlob',
    'd3'            : '../vendor/d3/d3',
    'domReady'      : '../vendor/requirejs-domready/domReady',
    'saveAs'     : '../vendor/FileSaver/FileSaver',
    'jquery'        : '../vendor/jquery/dist/jquery',
    'moment'        : '../vendor/moment/moment',
    'n3-line-chart' : '../vendor/n3-line-chart/dist/line-chart',
    'ngResource'    : '../vendor/angular-resource/angular-resource',
    'ui.router'     : '../vendor/angular-ui-router/release/angular-ui-router',
    'underscore'    : '../vendor/underscore/underscore'
  },

  shim: {
    'angular': {
      'deps': ['jquery'],
      'exports': 'angular'
    },
    'saveAs': ['canvas2blob'],
    'n3-line-chart': ['angular', 'd3', 'moment'],
    'ngResource': ['angular'],
    'ui.router' : ['angular']
  }
});
