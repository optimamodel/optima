define(['angular'], function (angular) {
  'use strict';

  return angular.module('app.open-help', [])
    .service('helpService', function () {
      this.openHelp = function ($modal, url) {
        return $modal.open({
          templateUrl: 'js/modules/programs/program-set/program-modal.html',
          size: 'lg'
        });
      }
    });
});

function helpController($scope, helpService){
  $scope.openHelp = helpService.openHelp;
}