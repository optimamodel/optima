define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ResponseController', function ($scope, $http, modalService) {

    $scope.state = {
      responses: [{name:'Default'}],
      activeResponseName: 'Default'
    };

    $scope.addResponse = function () {
      var add = function (name) {
        $scope.state.responses[$scope.state.responses.length] = {name:name};
        this.state.activeResponseName = name;
      };

      modalService.addResponse( add.bind(this) , $scope.state.responses);
    };

  });
});
