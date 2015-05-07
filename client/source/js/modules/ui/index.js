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

    .controller('MainCtrl', function ($scope, $state, activeProject, UserManager, modalService, fileUpload, PreventNavigation) {

      $scope.user = UserManager.data;
      $scope.userLogged = function () {
        return UserManager.isLoggedIn;
      };

      $scope.activeProject = activeProject;

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

      function ifActiveProject(state, name, activeProject) {
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
      }

      var confirmPopup = function (message, head, stateName, trigger) {
        modalService.confirm(
          function (){
            trigger();
            $state.go(stateName);
          },
          function (){},
          'Yes',
          'No',
          message,
          head
        );
      }
      $scope.$on('$stateChangeStart',function (event, toState, toParams, fromState, fromParams) {
        switch ( fromState.name ) {
          case 'model.view':
            if ( PreventNavigation.getCalibration() ) {
              event.preventDefault();
              var message = 'Are you sure you want to leave this page?';
              var head = 'You haven\'t saved calibration?';
              confirmPopup(message, head, toState.name, function () {
                PreventNavigation.setCalibration(false);
              });
            }
            break;
          case 'model.define-cost-coverage-outcome':
            if ( PreventNavigation.getCostcoverage() ) {
              event.preventDefault();
              var message = 'Are you sure you want to leave this page?';
              var head = 'You haven\'t saved model';
              confirmPopup(message, head, toState.name, function () {
                PreventNavigation.setCostcoverage(false);
              });
            }
            break;
          case 'analysis.optimization':
            if ( PreventNavigation.getOptimization() ) {
              event.preventDefault();
              var message = 'Are you sure you want to leave this page?';
              var head = 'You haven\'t saved optimization';
              confirmPopup(message, head, toState.name, function () {
                PreventNavigation.setOptimization(false);
              });
            }
            break;
          case 'analysis.scenarios':
            if ( PreventNavigation.getScenario() ) {
              event.preventDefault();
              var message = 'Are you sure you want to leave this page?';
              var head = 'You haven\'t saved new scenario(s)';
              confirmPopup(message, head, toState.name, function () {
                PreventNavigation.setScenario(false);
              });
            }
            break;
        }
      });
    });
});
