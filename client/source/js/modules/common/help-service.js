define(['angular' ], function (angular) {
  'use strict';

  return angular.module('app.common.help-service', [])

    .factory('helpService', ['$modal', function($modal) {

      function openHelp(helpURL) {
        var fullURL = 'http://optimamodel.com/man/'+helpURL; // Actual mapping is defined in mapping.json in the optimawebsite repository
        var scrh = screen.height;
        var scrw = screen.width;
        var h = scrh*0.8; // Height of window
        var w = scrw*0.6; // Width of window
        var t = scrh*0.1; // Position from top of screen -- centered
        var l = scrw*0.37; // Position from left of screen -- almost all the way right
        newwindow = window.open(fullURL,'Reference manual','width='+w + ',height='+h + ',top='+t + ',left='+l);
        if (window.focus) {
          newwindow.focus()
        }
        return false;
      }

      return {openHelp: openHelp};
    }]);
});
