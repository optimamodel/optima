define([
  'angular',
  './editable/index',
  './menu/index',
  './spreadsheet-upload-hint/index',
  './modal/modal-service',
  '../common/file-upload-service',
  '../common/active-project-service',
  '../user-manager/index'
], function (angular) {
  'use strict';

  return angular.module('app.ui', [
    'app.active-project',
    'app.ui.editable',
    'app.ui.modal',
    'app.common.file-upload',
    'app.ui.menu'
  ])

    .controller('MainCtrl', function ($scope, $state, $rootScope, activeProject, UserManager, modalService, fileUpload, PreventNavigation) {

      $rootScope.modelDict = {};

      $scope.initialize = function () {
        $scope.user = UserManager.data;
        $scope.activeProject = activeProject;
        $scope.setupSidebar();

        // Observes state change to prevent unwanted state loss due to navigation clicks.
        $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
          PreventNavigation.onStateChangeStart(event, toState, toParams, fromState, fromParams, $rootScope.modelDict);
        });
        $scope.$on('$stateChangeSuccess', function (event, toState, toParams, fromState, fromParams) {
          PreventNavigation.onStateChangeSuccess(event, toState, toParams, fromState, fromParams, $rootScope.modelDict);
        });
        

        var adminMenu = {
          title: 'Admin',
          matchingState: 'admin',
          subitems: [
            {
              title: 'Manage users',
              click: function() {
                $state.go('admin.manage-users');
              },
              state:{
                name: 'admin.manage-users'
              }
            },
            {
              title: 'Manage user projects',
              click: function() {
                $state.go('admin.manage-projects');
              },
              state:{
                name: 'admin.manage-projects'
              }
            }
          ]
        };

        if(UserManager.isAdmin){
          $scope.asideMenuSettings.items.unshift(adminMenu);
        }

      }; // $scope.initialize 

      $scope.setupSidebar = function () {
        $scope.asideMenuSettings = {
          items: [
            {
              title: 'Create/open project',
              id: 'create-load',
              matchingState: 'project',
              subitems: [
                {
                  title: 'Create new project',
                  state: {
                    name: 'project.create'
                  }
                },
                {
                  title: 'Open/manage projects',
                  state: {
                    name: 'project.open'
                  }
                },
                {
                  title: 'Upload Optima spreadsheet',
                  click: function () {
                    if (activeProject.isSet()) {
                    angular
                      .element('<input type="file">')
                      .change(function (event) {
                        fileUpload.uploadDataSpreadsheet($scope, event.target.files[0]);
                      })
                      .click();
                    } else {
                        modalService.inform(
                          function (){ },
                          'Okay',
                          'Create or open a project first.',
                          'Cannot proceed'
                        );
                    }
                  }
                },
                {
                  title: 'Upload new project',
                  state: {
                    name: 'project.upload'
                  }
                },
              ]
            },
            {
              title: 'View & calibrate model',
              id: 'create-load',
              matchingState: 'model',
              subitems: [
                {
                  title: 'View data & model calibration',
                  click: function() {
                    ifActiveProject($state, 'model.view', activeProject);
                  },
                  state: {
                    name: 'model.view'
                  }
                },
                {
                  title: 'Define cost-coverage-outcome assumptions',
                  click: function() {
                    ifActiveProject($state, 'model.define-cost-coverage-outcome', activeProject);
                  },
                  state:{
                    name: 'model.define-cost-coverage-outcome'
                  }
                }
              ]
            },
            {
              title: 'Analysis',
              matchingState: 'analysis',
              subitems: [
                {
                  title: 'Scenario analyses',
                  click: function() {
                    ifActiveProject($state, 'analysis.scenarios', activeProject);
                  },
                  state:{
                    name: 'analysis.scenarios'
                  }
                },
                {
                  title: 'Optimization analyses',
                  click: function() {
                    ifActiveProject($state, 'analysis.optimization', activeProject);
                  },
                  state:{
                    name: 'analysis.optimization'
                  }
                }
              ]
            }
          ]
        };
      };

      /**
      * Anaswers true if the user is logged in, false otherwise.
      */
      $scope.userLogged = function () {
        return UserManager.isLoggedIn;
      };

      function ifActiveProject (state, name, activeProject) {
        if(activeProject.isSet()){
          state.go(name);
        } else {
            modalService.inform(
              function (){ },
              'Okay',
              'Create or open a project first.',
              'Cannot proceed'
            );
         }
      };

      $scope.initialize();
    });
});
