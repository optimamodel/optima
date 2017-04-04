define(['angular' ], function (angular) {
  'use strict';

  function openHelp(helpURL) {
    var fullURL = 'http://optimamodel.com/man/' + helpURL; // Actual mapping is defined in mapping.json in the optimawebsite repository
    console.log('openHelp ', fullURL)
    var scrh = screen.height;
    var scrw = screen.width;
    var h = scrh * 0.8; // Height of window
    var w = scrw * 0.6; // Width of window
    var t = scrh * 0.1; // Position from top of screen -- centered
    var l = scrw * 0.37; // Position from left of screen -- almost all the way right
    var newwindow = window.open(fullURL, 'Reference manual', 'width=' + w + ',height=' + h + ',top=' + t + ',left=' + l);
    if (window.focus) {
      newwindow.focus()
    }
    return false;
  }

  var module = angular.module('app.common.help-service', []);

  module.directive('help', function() {
    return {
      restrict: 'E',
      template:
        '<a '
          + 'class="fa fa-question-circle-o"'
          + 'tp-text="Help" tooltip tp-class="tooltip"'
          + 'tp-x="-50" tp-y="-150" tp-anchor-x="0" tp-anchor-y="0"'
          + 'style="margin-left: 0.5em; color: #29abe2; font-size: 14px"'
          + 'ng-click="run()"'
          + '>'
        ,
      link: function(scope, elem, attrs) {
        scope.run = function(info) { openHelp(attrs['ref']); };
      }
    }
  })

});
