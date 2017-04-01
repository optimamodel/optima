define(['angular' ], function (angular) {
  'use strict';

  return angular.module('app.common.help-service', [])

    .factory('helpService', ['$modal', function($modal) {

      function openHelp(helpURL) {
        var fullURL = 'http://optimamodel.com/man/'+helpURL;
        var scrh = screen.height;
        var scrw = screen.width;
        var h = scrh*0.8; // Height of window
        var w = scrw*0.5; // Width of window
        var t = scrh*0.1; // Position from top of screen
        var l = scrw*0.4; // Position from left of screen
        newwindow = window.open(fullURL,'Reference manual','width='+w + ',height='+h + ',top='+t + ',left='+l);
        if (window.focus) {
          newwindow.focus()
        }
        return false;
      }

      return {openHelp: openHelp};
    }]);
});
