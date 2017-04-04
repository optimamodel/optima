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
        '<i '
          + 'class="fa fa-question-circle-o"'
          + 'tp-text="Help" tooltip tp-class="tooltip"'
          + 'tp-x="-50" tp-y="-150" tp-anchor-x="0" tp-anchor-y="0"'
          + 'style="margin-left: 0.5em; color: #29abe2; font-size: 14px"'
          + 'ng-click="run()"'
          + '></i>'
        ,
      link: function(scope, elem, attrs) {
        scope.run = function(info) { openHelp(attrs['ref']); };
      }
    }
  });

  // <icon action="copy" click="someFn()"/>

  module.directive('icon', function($compile) {

    var iconTypes = {
      'copy': { iconName: 'fa-copy', helpText: 'Copy'},
      'new': { iconName: 'fa-file-o', helpText: 'New'},
      'edit': { iconName: 'fa-pencil', helpText: 'Edit'},
      'delete': { iconName: 'fa-trash-o', helpText: 'Delete'},
      'upload': { iconName: 'fa-upload', helpText: 'Upload'},
      'download': { iconName: 'fa-download', helpText: 'Download'},
    };

    return {
      restrict: 'E',
      scope: {
        click: '&',
        action: '@'
      },
      link: function(scope, element){
        var html =
          '<i'
          + ' class="fa ' + iconTypes[scope.action].iconName + '"'
          + ' tp-text="' + iconTypes[scope.action].helpText + '" '
          + ' tooltip tp-class="tooltip" '
          + ' tp-x="-50" tp-y="-150" '
          + ' tp-anchor-x="0" tp-anchor-y="0"'
          + ' style="margin-left: 0.5em; font-size: 14px"'
          + ' ng-click="click()"'
          + '></i>';
        var el = $compile(html)(scope);
        element.append(el);
      }
    }
  });

});
