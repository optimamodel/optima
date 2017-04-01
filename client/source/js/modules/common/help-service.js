define(['angular' ], function (angular) {
  'use strict';

  return angular.module('app.common.help-service', [])

    .factory('helpService', ['$modal', function($modal) {

      function openHelp(helpURL) {
        var fullURL = 'http://optimamodel.com/man/'+helpURL;
        var h = screen.height*0.8;
        var w = screen.width*0.5;
        newwindow = window.open(fullURL,'Reference manual','width='+w +',height=' +h);
        if (window.focus) {
          newwindow.focus()
        }
        return false;
      }

      return {openHelp: openHelp};
    }]);
});
