define(['angular'], function (angular) {

  'use strict';

  return angular
    .module('app.menu', ['app.user-manager'])
    .directive('menu', function(
      $state, userManager, projectService, rpcService, modalService) {

      return {
        restrict: 'A',
        scope: {settings: '= menu'},
        templateUrl: 'js/modules/ui/menu.html',
        controller: ['$scope', function($scope) {

          $scope.state = $state.current;
          $scope.isAdmin = userManager.isAdmin;

          $scope.getState = function() {
            return $state.current.name;
          };

          $scope.isState = function(testName) {
            return $scope.getState().indexOf(testName) !== -1;
          };

          $scope.checkCalibration = function() {
            return projectService.calibrationOK;
          };

          $scope.checkPrograms = function() {
            return projectService.programsOK;
          };

          $scope.checkCostFuncs = function() {
            return projectService.costFuncsOK;
          };

          $scope.goIfProjectActive = function(stateName) {
            if(projectService.isActiveProjectSet()){
              console.log('current state', $state.current.name, '->', stateName);
              $state.go(stateName);
            } else {
              modalService.inform(
                function () {},
                'Okay',
                'Create or open a project first.',
                'Cannot proceed'
              );
            }
          };



          $scope.logout = function() {
            rpcService
              .rpcRun('do_logout_current_user')
              .then(function() {
                 window.location.reload();
              })
          };

        }]
      };
    });
});
