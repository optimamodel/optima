define(['angular', '../common/local-storage-polyfill'], function (angular) {
  'use strict';

  var module = angular.module('app.common.project-service', []);

  module.service('projectService',
    ['$http', '$q', 'userManager', 'utilService', function ($http, $q, userManager, utilService) {

      var projectService = {
        projects: [],
        project: {},
      };

      function makeUserKey(userId) {
        return 'activeProjectFor:' + userId;
      }

      function setActiveProjectId(projectId) {
        projectService.project.id = projectId;
        var projectStr = JSON.stringify(projectService.project);
        localStorage[makeUserKey(userManager.user.id)] = projectStr;
      }

      function loadActiveProject() {
        var projectStr = localStorage[makeUserKey(userManager.user.id)];
        if (projectStr !== null && projectStr !== undefined) {
          try {
            projectService.project = JSON.parse(projectStr);
          } catch (exception) {
          }
        }
      }

      function clearProjectIdIfActive(projectId) {
        if (projectService.project.id === projectId) {
          delete projectService.project.id;
          localStorage.removeItem(makeUserKey(userManager.user.id));
        }
      }

      function clearProjectForUserId(userId) {
        localStorage.removeItem(makeUserKey(userId));
      }

      function isActiveProjectSet() {
        return (projectService.project.id !== null && projectService.project.id !== undefined);
      }

      function clearList(aList) {
        while (aList.length) {
          aList.pop(0);
        }
      }

      function getProjectAndMakeActive(projectId) {
        var deferred = $q.defer();
        utilService
          .rpcRun(
            'load_project_summary', [projectId])
          .then(
            function(response) {
              var uploadedProject = response.data;
              var existingProject = _.findWhere(
                projectService.projects, {id: uploadedProject.id});
              if (existingProject) {
                console.log('getProjectAndMakeActive update', uploadedProject);
                _.extend(existingProject, uploadedProject);
              } else {
                console.log('getProjectAndMakeActive new', uploadedProject);
                projectService.projects.push(uploadedProject);
              }
              setActiveProjectId(uploadedProject.id);
              deferred.resolve(response);
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function getProjectList() {
        var deferred = $q.defer();
        utilService
          .rpcRun(
            'load_current_user_project_summaries')
          .then(
            function(response) {
              clearList(projectService.projects);
              _.each(response.data.projects, function(project) {
                project.creationTime = Date.parse(project.creationTime);
                project.updatedTime = Date.parse(project.updatedTime);
                project.dataUploadTime = Date.parse(project.dataUploadTime);
                projectService.projects.push(project);
              });
              deferred.resolve(response);
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function getOptimaLiteProjectList() {
        var deferred = $q.defer();
        utilService
          .rpcRun(
            'get_optimalite_projects')
          .then(
            function(response) {
              clearList(projectService.optimaliteprojects);
              _.each(response.data.projects, function(project) {
                project.creationTime = Date.parse(project.creationTime);
                project.updatedTime = Date.parse(project.updatedTime);
                project.dataUploadTime = Date.parse(project.dataUploadTime);
                projectService.optimaliteprojects.push(project);
              });
              deferred.resolve(response);
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function createProject(project) {
        var deferred = $q.defer();
        utilService
          .rpcRun('create_project', [userManager.user.id, project])
          .then(
            function(response) {
              getProjectAndMakeActive(response.data.projectId);
              utilService
                .rpcDownload('download_template', [project])
                .then(
                  function(response) { deferred.resolve(response); },
                  function(response) { deferred.reject(response); });
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function uploadProject() {
        var deferred = $q.defer();
        var otherNames = _.pluck(projectService.projects, 'name');
        utilService
          .rpcUpload(
            'create_project_from_prj_file',
            [userManager.user.id, otherNames])
          .then(
            function(response) {
              getProjectAndMakeActive(response.data.projectId)
                .then(
                  function(response) { deferred.resolve(response); },
                  function(response) { deferred.reject(response); });
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function uploadProjectFromSpreadsheet() {
        var deferred = $q.defer();
        var otherNames = _.pluck(projectService.projects, 'name');
        utilService
          .rpcUpload(
            'create_project_from_spreadsheet',
            [userManager.user.id, otherNames])
          .then(
            function(response) {
              getProjectAndMakeActive(response.data.projectId)
                .then(
                  function(response) { deferred.resolve(response); },
                  function(response) { deferred.reject(response); });
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function copyProject(projectId, newName) {
        var deferred = $q.defer();
        utilService
          .rpcRun(
            'copy_project', [projectId, newName])
          .then(
            function(response) {
              console.log('copyProject', response);
              getProjectAndMakeActive(response.data.projectId)
                .then(
                  function(response) { deferred.resolve(response); },
                  function(response) { deferred.reject(response); });
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function renameProject(id, project) {
        var deferred = $q.defer();
        utilService
          .rpcRun(
            'update_project_from_summary', [project])
          .then(
            function(response) {
              setActiveProjectId(project.id);
              deferred.resolve(response);
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      function deleteProjects(projectIds) {
        var deferred = $q.defer();
        utilService
          .rpcRun(
            'delete_projects', [projectIds])
          .then(
            function(response) {
              console.log('deleteProjects', projectIds);
              _.each(projectIds, function(projectId) {
                clearProjectIdIfActive(projectId);
              });
              var iInit = projectService.projects.length - 1;
              for (var i=iInit; i>=0; i-=1) {
                var p = projectService.projects[i];
                if (_.contains(projectIds, p.id)) {
                  projectService.projects.splice(i, 1);
                }
              }
              deferred.resolve(response);
            },
            function(response) {
              deferred.reject(response);
            });
        return deferred.promise;
      }

      getProjectList();
      getOptimaLiteProjectList();

      _.assign(projectService, {
        getProjectList: getProjectList,
        setActiveProjectId: setActiveProjectId,
        loadActiveProject: loadActiveProject,
        clearProjectIdIfActive: clearProjectIdIfActive,
        clearProjectForUserId: clearProjectForUserId,
        isActiveProjectSet: isActiveProjectSet,
        copyProject: copyProject,
        renameProject: renameProject,
        createProject: createProject,
        deleteProjects: deleteProjects,
        uploadProject: uploadProject,
        uploadProjectFromSpreadsheet: uploadProjectFromSpreadsheet,
        getActiveProject: function () {
          var projectId = projectService.project.id;
          if (projectId) {
            return getProjectAndMakeActive(projectId);
          }
        },
        downloadSelectedProjects: function (projectIds) {
          return utilService.rpcDownload('load_zip_of_prj_files', [projectIds]);
        },
        getAllProjectList: function () {
          return utilService.rpcRun('load_all_project_summaries');
        },
        getPopulations: function () {
          return utilService.rpcRun('get_default_populations');
        },
        getDefaultPrograms: function (projectId) {
          return utilService.rpcRun('load_project_program_summaries', [projectId]);
        },
      });

      return projectService;

    }]);
});
