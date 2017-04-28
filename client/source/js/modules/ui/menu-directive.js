define(['angular'], function (angular) {

  'use strict';

  return angular
    .module('app.ui.menu', ['app.user-manager'])
    .directive('menu', function(
      $state, userManager, projectService, utilService, modalService) {

      return {
        restrict: 'A',
        scope: {settings: '= menu'},
        templateUrl: 'js/modules/ui/menu.html',
        controller: ['$scope', function($scope) {

          $scope.state = $state.current;
          $scope.isAdmin = userManager.isAdmin;
          $scope.programsDefined = projectService.project.programsDefined;

          $scope.getState = function() {
            return $state.current.name;
          };

          $scope.isState = function(testName) {
            return $scope.getState().indexOf(testName) !== -1;
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
            utilService
              .rpcRun('do_logout_current_user')
              .then(function() {
                 window.location.reload();
              })
          };

        }]
      };
    });
});
