define(['./../module', 'angular', 'underscore'], function (module, angular, _) {
  'use strict';

  module.controller('ProjectSetController', function ($scope, $http, projectSetModalService, $timeout, modalService, predefined) {

    const defaultProjectSet = {name:'Default'};
    $scope.state = {
      projectSetList: [defaultProjectSet],
      activeProjectSet: defaultProjectSet
    };

    $scope.addProjectSet = function () {
      var add = function (name) {
        const addedProjectSet = {name:name};
        $scope.state.projectSetList[$scope.state.projectSetList.length] = addedProjectSet;
        $scope.state.activeProjectSet = addedProjectSet;
      };

      projectSetModalService.addProjectSet( add , $scope.state.projectSetList);
    };

    $scope.editProjectSet = function () {
      // This removing existing enter from array of projectSetList and re-adding it with updated name was needed,
      // coz it turns out that angular does not refreshes the select unless there is change in its size.
      // https://github.com/angular/angular.js/issues/10939
      var edit = function (name) {
        $scope.state.projectSetList = _.filter($scope.state.projectSetList, function(projectSet) {
          return projectSet.name !== $scope.state.activeProjectSet.name;
        });
        $timeout(function(){
          $scope.state.activeProjectSet.name = name;
          $scope.state.projectSetList[$scope.state.projectSetList.length] = $scope.state.activeProjectSet;
        });
      };
      projectSetModalService.editProjectSet($scope.state.activeProjectSet.name, edit , $scope.state.projectSetList);
    };

    $scope.deleteProjectSet = function () {
      var remove = function() {
        $scope.state.projectSetList = _.filter($scope.state.projectSetList, function(projectSet) {
          return projectSet.name !== $scope.state.activeProjectSet.name;
        });
        $scope.state.activeProjectSet = $scope.state.projectSetList ? $scope.state.projectSetList[0] : void 0;
      };
      modalService.confirm(
        function(){remove()}, function(){}, 'Yes, remove this projectSet', 'No',
        'Are you sure you want to permanently remove projectSet "' + $scope.state.activeProjectSet.name + '"?',
        'Remove projectSet'
      );
    };

    $scope.copyProjectSet = function () {
      // TODO: program details to also be copied
      var copy = function (name) {
        const copiedProjectSet = {name:name};
        $scope.state.projectSetList[$scope.state.projectSetList.length] = copiedProjectSet;
        $scope.state.activeProjectSet = copiedProjectSet;
      };
      projectSetModalService.copyProjectSet($scope.state.activeProjectSet.name, copy.bind(this) , $scope.state.projectSetList);
    };

    $scope.categories = predefined.categories;
    $scope.programs = predefined.programs;

  });
});