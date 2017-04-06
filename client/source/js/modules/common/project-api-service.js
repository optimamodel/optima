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

    function isSet() {
      return (projectApi.project.id !== null && projectApi.project.id !== undefined);
    }

    function getProjectList() {
      var deferred = $q.defer();
      $http
        .get(
          '/api/project')
        .then(
          function(response) {
            while (projectApi.projects.length) {
              projectApi.projects.pop(0);
            }
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

    function copyProject(projectId, newName) {
      var deferred = $q.defer();
      $http
        .post(
          '/api/project/' + projectId + '/copy', {to: newName})
        .then(
          function(response) {
            projectApi
              .getProjectList()
              .then(function(response) {
                var project = _.findWhere(projectApi.projects, {name: newName});
                console.log('copyProject', project, projectApi.projects);
                setActiveProjectId(project.id);
                deferred.resolve(response);
              });
          },
          function(response) {
            deferred.reject(response);
          });
      return deferred.promise;
    }

    function renameProject(id, project) {
      var deferred = $q.defer();
      $http
        .put(
          '/api/project/' + id,
          {
            project: project,
            isSpreadsheet: false,
            isDeleteData: false,
          },
          {responseType: 'blob'})
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

    function deleteProject(projectId) {
      var deferred = $q.defer();
      $http
        .delete('/api/project/' + projectId)
        .then(
          function(response) {
            var n = projectApi.projects.length;
            for (var i=0; i<projectApi.projects.length; i+=1) {
              if (projectApi.projects[i].id == projectId) {
                projectApi.projects.splice(i, 1);
              }
            }
            clearProjectIdIfActive(projectId);
            deferred.resolve(response);
          },
          function(response) {
            deferred.reject(response);
          });
      return deferred.promise;
    }

    function createProject(projectParams) {
      var deferred = $q.defer();
      $http
        .post(
          '/api/project', projectParams, {responseType:'blob'})
        .then(
          function(response) {
            projectApi
              .getProjectList()
              .then(function(response) {
                console.log('createProject', projectParams);
                var project = _.findWhere(
                  projectApi.projects, {name: projectParams.name});
                setActiveProjectId(project.id);
                if (response.data) {
                  var blob = new Blob(
                    [response.data],
                    {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
                  saveAs(blob, (projectParams.name + '.xlsx'));
                }
                deferred.resolve(response);
              });
          },
          function(response) {
            deferred.reject(response);
          });
      return deferred.promise;
    }

    function deleteSelectedProjects(projects) {
      var deferred = $q.defer();
      $http({
          method: 'DELETE',
          url: '/api/project',
          data: {projects: projects}
        })
        .then(
          function(response) {
            projectApi
              .getProjectList()
              .then(function() {
                _.each(projects, function(project) {
                  clearProjectIdIfActive(project.id);
                });
                deferred.resolve(response);
              });
          },
          function(response) {
            deferred.reject(response);
          });
      return deferred.promise;
    }

    function uploadProject() {
      var deferred = $q.defer();
      util
        .rpcUpload(
          'create_project_from_prj', [userManager.user.id])
        .then(function(response) {
          var projectId = response.data.projectId;
          projectApi
            .getProjectList()
            .then(
              function(response) {
                var project = _.findWhere(
                  projectApi.projects, {id: projectId});
                setActiveProjectId(project.id);
                deferred.resolve(response);
              },
              function(response) {
                deferred.reject(response);
              });
        });
      return deferred.promise;
    }

    function uploadProjectFromSpreadsheet() {
      var deferred = $q.defer();
      util
        .rpcUpload(
          'create_project_from_spreadsheet', [userManager.user.id])
        .then(function(response) {
          var projectId = response.data.projectId;
          console.log('uploadProject', projectId);
          projectApi
            .getProjectList()
            .then(
              function(response) {
                var project = _.findWhere(
                  projectApi.projects, {id: projectId});
                setActiveProjectId(project.id);
                deferred.resolve(response);
              },
              function(response) {
                deferred.reject(response);
              });
        });
      return deferred.promise;
    }

    getProjectList();

    _.assign(projectApi, {
      setActiveProjectId: setActiveProjectId,
      loadActiveProject: loadActiveProject,
      clearProjectIdIfActive: clearProjectIdIfActive,
      clearProjectForUserId: clearProjectForUserId,
      isSet: isSet,
      getProjectList: getProjectList,
      copyProject: copyProject,
      renameProject: renameProject,
      createProject: createProject,
      deleteProject: deleteProject,
      deleteSelectedProjects: deleteSelectedProjects,
      uploadProject: uploadProject,
      uploadProjectFromSpreadsheet: uploadProjectFromSpreadsheet,
      getActiveProject: function () {
        var projectId = projectApi.project.id;
        if (projectId) {
          return $http.get('/api/project/' + projectId);
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
