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

    .controller('MainCtrl', function ($scope, $state, activeProject, UserManager, modalService, fileUpload) {

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
              }
            ]
          },
          {
            title: 'View data & model calibration',
            id: 'create-load',
            click: function() {
              ifActiveProject($state, 'model', activeProject);
            },
            state: {
              name: 'model'
            }
          },
          {
            title: 'Create/manage project set',
            id: 'manage-responses',
            matchingState: 'project-set',
            subitems: [
              {
                title: 'Define programs',
                click: function() {
                  ifActiveProject($state, 'project-set.manageProgramSet', activeProject);
                },
                state: {
                  name: 'project-set.manageProgramSet'
                }
              },
              {
                title: 'Define cost and outcome functions',
                click: function() {
                  ifActiveProject($state, 'project-set.define-cost-coverage-outcome', activeProject);
                },
                state:{
                  name: 'project-set.define-cost-coverage-outcome'
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

    });
});
