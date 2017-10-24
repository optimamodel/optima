define(
  ['angular', '../common/project-service', '../user/user-manager-service'],
  function (angular) {

    'use strict';

    var module = angular.module(
      'app.main', ['app.project-service', 'app.user-manager']);

    /**
     * This controller is for displaying the user/project
     * in the top-right hand corner of every page
     */
    module.controller(
      'MainCtrl',
      function($scope, $state, userManager, projectService) {

        $scope.user = userManager.user;
        $scope.state = $state;
        $scope.userLogged = function() {
          return userManager.isLoggedIn;
        };
        $scope.projectService = projectService;
        $scope.projects = projectService.projects;
        $scope.changeProject = function(projectId) {
          var project = _.findWhere($scope.projects, {id: projectId});
          console.log('changeProject', project.name);
          projectService.setActiveProjectId(projectId);
        };

      });

    return module;

});
