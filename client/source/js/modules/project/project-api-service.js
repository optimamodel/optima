define(['./module'], function (module) {
  'use strict';

  module.service('projectApi',
    [ '$http', '$q', 'activeProject', 'userManager', 'util',
      function ($http, $q, activeProject, userManager, util) {

    var projectApi = {
      projects: []
    };

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
                var project = _.findWhere(
                  projectApi.projects, {name: newName});
                console.log('copyProject', project, projects);
                activeProject.setActiveProjectFor(
                  project.name, project.id, userManager.user);
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
            activeProject.setActiveProjectFor(
              project.name, project.id, userManager.user);
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
            activeProject.ifActiveResetFor(projectId, userManager.user);
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
                activeProject.setActiveProjectFor(
                  project.name, project.id, userManager.user);
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
                  activeProject.ifActiveResetFor(project.id, userManager.user);
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
                activeProject.setActiveProjectFor(
                  project.name, project.id, userManager.user)
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
                activeProject.setActiveProjectFor(
                  project.name, project.id, userManager.user)
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
      getProjectList: getProjectList,
      copyProject: copyProject,
      renameProject: renameProject,
      createProject: createProject,
      deleteProject: deleteProject,
      deleteSelectedProjects: deleteSelectedProjects,
      uploadProject: uploadProject,
      uploadProjectFromSpreadsheet: uploadProjectFromSpreadsheet,
      getActiveProject: function () {
        var projectId = activeProject.project.id;
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
      downloadProjectFile: function(projectId) {
        return $http.get(
          '/api/project/' + projectId + '/data',
          {
            headers: {'Content-type': 'application/octet-stream'},
            responseType: 'blob'
          });
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
