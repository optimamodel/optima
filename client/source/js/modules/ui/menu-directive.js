define(['angular'], function (angular) {

  'use strict';

  return angular
    .module('app.ui.menu', ['app.user-manager'])
    .directive('menu', function(
      $state, userManager, activeProject, modalService, $http) {

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

          $scope.goIfProjectActive = function(stateName) {
            if(activeProject.isSet()){
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
            $http
              .get('/api/user/logout')
              .success(function() { window.location.reload(); });
          };

        }]
      };
    });
});
