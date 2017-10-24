if (typeof define !== 'function') {
  // to be able to require file from node
  var define = require('amdefine')(module);
}

define({
  waitSeconds: 300, // timeout after 5min

  // Here paths are set relative to `source` folder
  paths: {
    'underscore': './vendor/underscore/underscore',
    'jquery': './vendor/jquery/dist/jquery',
    'ng-file-upload-html5-shim': './vendor/ng-file-upload/angular-file-upload-shim',
    'angular': './vendor/angular/angular',
    'ng-loading-bar': './vendor/angular-loading-bar/build/loading-bar',
    'ng-resource': './vendor/angular-resource/angular-resource',
    'ng-file-upload': './vendor/ng-file-upload/angular-file-upload',
    'toastr': './vendor/angular-toastr/dist/angular-toastr.tpls',
    'ui.router': './vendor/angular-ui-router/release/angular-ui-router',
    'ui.bootstrap': './vendor/angular-bootstrap/ui-bootstrap-tpls',
    'tooltip': './vendor/tooltip/dist/tooltip',
    'rzModule': './vendor/angularjs-slider/dist/rzslider.min',
    'd3': './vendor/d3/d3',
    'mpld3': './js/modules/charts/mpld3.v0.3.1.dev1',
    'canvas2blob': './vendor/canvas-toBlob.js/canvas-toBlob',
    'saveAs': './vendor/FileSaver/FileSaver',
    'jsPDF': './vendor/jspdf/dist/jspdf.min',
    'sha224': './js/modules/user/sha224'
  },

  shim: {
    'angular': {
      'deps': ['ng-file-upload-html5-shim', 'jquery'],
      'exports': 'angular'
    },
    'ng-loading-bar': ['angular'],
    'ng-resource': ['angular'],
    'ng-file-upload': ['angular'],
    'ui.bootstrap': ['angular'],
    'ui.router' : ['angular'],
    'tooltip': ['angular'],
    'rzModule': ['angular'],
    'toastr': ['angular'],
    'saveAs': ['canvas2blob'],
    'mpld3' : {
      'deps': ['d3'],
      'exports': 'mpld3'
    }
  }
});
