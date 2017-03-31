//define(['angular'], function (angular) {
//  'use strict';
//
//  return angular.module('app.open-help', [])
//    .service('helpService', function () {
//      this.openHelp = function ($modal, url) {
//        return $modal.open({
//          templateUrl: 'js/modules/programs/program-set/program-modal.html',
//          size: 'lg'
//        });
//      }
//    });
//});



define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('HelpModalController', function (
    $scope, $modal, helpURL) {

    function openHelpModal(helpURL) {
      return $modal.open({
        templateUrl: 'js/modules/programs/program-set/program-modal.html',
        size: 'lg'
      });
    }

  });

});
