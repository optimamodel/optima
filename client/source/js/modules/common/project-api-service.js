define(['angular', '../common/local-storage-polyfill'], function (angular) {
  'use strict';

  var module = angular.module('app.common.project-api-service', []);

  module.service('projectApi',
    ['$http', '$q', 'userManager', 'util', function ($http, $q, userManager, util) {

    var projectApi = {
      projects: [],
      project: {},
    };

    function makeUserKey(userId) {
      return 'activeProjectFor:' + userId;
    }

    function setActiveProjectId(projectId) {
      projectApi.project.id = projectId;
      var projectStr = JSON.stringify(projectApi.project);
      localStorage[makeUserKey(userManager.user.id)] = projectStr;
    }

    function loadActiveProject() {
      var projectStr = localStorage[makeUserKey(userManager.user.id)];
      if (projectStr !== null && projectStr !== undefined) {
        try {
          projectApi.project = JSON.parse(projectStr);
        } catch (exception) {
        }
      }
    }

    function clearProjectIdIfActive(projectId) {
      if (projectApi.project.id === projectId) {
        delete projectApi.project.id;
        localStorage.removeItem(makeUserKey(userManager.user.id));
      }
    }

    function clearProjectForUserId(userId) {
      localStorage.removeItem(makeUserKey(userId));
    }

    function isActiveProjectSet() {
      return (projectApi.project.id !== null && projectApi.project.id !== undefined);
    }

    function clearList(aList) {
      while (aList.length) {
        aList.pop(0);
      }
    }

    function getProjectAndMakeActive(projectId) {
      var deferred = $q.defer();
      util
        .rpcRun(
          'load_project_summary', [projectId])
        .then(
          function(response) {
            var uploadedProject = response.data;
            var existingProject = _.findWhere(
              projectApi.projects, {id: uploadedProject.id});
            if (existingProject) {
              console.log('getProjectAndMakeActive update', uploadedProject);
              _.extend(existingProject, uploadedProject);
            } else {
              console.log('getProjectAndMakeActive new', uploadedProject);
              projectApi.projects.push(uploadedProject);
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
      util
        .rpcRun(
          'load_project_summaries', [userManager.user.id])
        .then(
          function(response) {
            clearList(projectApi.projects);
            _.each(response.data.projects, function(project) {
              project.creationTime = Date.parse(project.creationTime);
              project.updatedTime = Date.parse(project.updatedTime);
              project.dataUploadTime = Date.parse(project.dataUploadTime);
              projectApi.projects.push(project);
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
      util
        .rpcRun('create_project', [userManager.user.id, project])
        .then(
          function(response) {
            getProjectAndMakeActive(response.data.projectId);
            util
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
      var otherNames = _.pluck(projectApi.projects, 'name');
      util
        .rpcUpload(
          'create_project_from_prj',
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
      var otherNames = _.pluck(projectApi.projects, 'name');
      util
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
      util
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
      util
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
      util
        .rpcRun(
          'delete_projects', [projectIds])
        .then(
          function(response) {
            console.log('deleteProjects', projectIds);
            _.each(projectIds, function(projectId) {
              clearProjectIdIfActive(projectId);
            });
            var iInit = projectApi.projects.length - 1;
            for (var i=iInit; i>=0; i-=1) {
              var p = projectApi.projects[i];
              if (_.contains(projectIds, p.id)) {
                projectApi.projects.splice(i, 1);
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

    _.assign(projectApi, {
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
        var projectId = projectApi.project.id;
        if (projectId) {
          return getProjectAndMakeActive(projectId);
        }
      },
      downloadSelectedProjects: function(projects) {
        return $http.post(
          '/api/project/portfolio',
          {projects: projects},
          {responseType: 'arraybuffer'});
      },
      getAllProjectList: function () {
        return $http.get('/api/project/all');
      },
      getPopulations: function () {
        return $http.get('/api/project/populations');
      },
      getDefaultPrograms: function (projectId) {
        return $http.get('/api/project/' + projectId + '/defaults');
      },
      getSpreadsheetUrl: function(id) {
        return '/api/project/' + id + '/spreadsheet';
      }
    });

    return projectApi;

  }]);
});
