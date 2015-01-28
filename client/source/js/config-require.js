if (typeof define !== 'function') {
  // to be able to require file from node
  var define = require('amdefine')(module);
}

define({
  // Here paths are set relative to `/source/js` folder
  paths: {
    'angular'       : './vendor/angular/angular',
    'angular-loading-bar'  : './js/modules/angular-loading-bar/loading-bar',
    'async'         : './vendor/requirejs-plugins/src/async',
    'canvg'         : './vendor/canvg/dist/canvg.bundle',
    'canvas2blob'   : './vendor/canvas-toBlob.js/canvas-toBlob',
    'crypto'        : './vendor/crypto-js-evanvosberg/build/rollups/sha224',
    'd3'            : './vendor/d3/d3',
    'd3-tip'        : './vendor/d3-tip/index',
    'saveAs'        : './vendor/FileSaver/FileSaver',
    'jquery'        : './vendor/jquery/dist/jquery',
    'jsPDF'         : './vendor/jspdf/dist/jspdf.min',
    'ng-file-upload': './vendor/ng-file-upload/angular-file-upload',
    'ng-file-upload-html5-shim': './vendor/ng-file-upload/angular-file-upload-html5-shim',
    'numeral'       : './/vendor/numeral/numeral',
    'angular-resource'    : './vendor/angular-resource/angular-resource',
    'radar-chart-d3' : './vendor/radar-chart-d3/src/radar-chart',
    'ui.router'     : './vendor/angular-ui-router/release/angular-ui-router',
    'ui.bootstrap'  : './vendor/angular-bootstrap/ui-bootstrap-tpls',
    'underscore'    : './vendor/underscore/underscore',
  },

  shim: {
    'angular': {
      'deps': ['ng-file-upload-html5-shim', 'jquery'],
      'exports': 'angular'
    },
    'angular-loading-bar': ['angular'],
    'd3-box': ['d3'],
    'd3-tip': ['d3'],
    'angular-resource': ['angular'],
    'ng-file-upload': ['angular'],
    'radar-chart-d3': ['d3'],
    'saveAs': ['canvas2blob'],
    'ui.bootstrap': ['angular'],
    'ui.router' : ['angular']
  }
});
