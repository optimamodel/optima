if (typeof define !== 'function') {
  // to be able to require file from node
  var define = require('amdefine')(module);
}

define({
  // Here paths are set relative to `/source/js` folder
  paths: {
    'angular'       : '../vendor/angular/angular',
    'angular-nvd3'  : '../vendor/angular-nvd3/dist/angular-nvd3',
    'async'         : '../vendor/requirejs-plugins/src/async',
    'canvg'         : '../vendor/canvg/dist/canvg.bundle',
    'canvas2blob'   : '../vendor/canvas-toBlob.js/canvas-toBlob',
    'd3'            : '../vendor/d3/d3',
    'domReady'      : '../vendor/requirejs-domready/domReady',
    'saveAs'        : '../vendor/FileSaver/FileSaver',
    'jquery'        : '../vendor/jquery/dist/jquery',
    'nvd3'          : '../vendor/nvd3/nv.d3',
    'ngResource'    : '../vendor/angular-resource/angular-resource',
    'ui.router'     : '../vendor/angular-ui-router/release/angular-ui-router',
    'underscore'    : '../vendor/underscore/underscore'
  },

  shim: {
    'angular': {
      'deps': ['jquery'],
      'exports': 'angular'
    },
    'angular-nvd3': ['angular', 'nvd3'],
    'nvd3': ['d3'],
    'ngResource': ['angular'],
    'saveAs': ['canvas2blob'],
    'ui.router' : ['angular']
  }
});
