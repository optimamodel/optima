define(['./module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ResponseController', function ($scope, $http, modalService, $timeout) {

    const defaultResponse = {name:'Default'};
    $scope.state = {
      responses: [defaultResponse],
      activeResponse: defaultResponse
    };

    $scope.addResponse = function () {
      var add = function (name) {
        const addedResponse = {name:name};
        $scope.state.responses[$scope.state.responses.length] = addedResponse;
        $scope.state.activeResponse = addedResponse;
      };

      modalService.addResponse( add.bind(this) , $scope.state.responses);
    };

    $scope.editResponse = function () {
      // This removing existing enter from array of responses and re-adding it with updated name was needed,
      // coz it turns out that angular does not refreshes the select unless there is change in its size.
      // https://github.com/angular/angular.js/issues/10939
      var edit = function (name) {
        $scope.state.responses = _.filter($scope.state.responses, function(response) {
          return response.name !== $scope.state.activeResponse.name;
        });
        $timeout(function(){
          $scope.state.activeResponse.name = name;
          $scope.state.responses[$scope.state.responses.length] = $scope.state.activeResponse;
        });
      };
      modalService.editResponse($scope.state.activeResponse.name, edit.bind(this) , $scope.state.responses);
    };
  });
});
