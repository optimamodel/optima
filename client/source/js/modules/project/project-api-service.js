define(['./module'], function (module) {
  'use strict';

  module.service('projectApi',
    [ '$http', '$q', 'activeProject', function ($http, $q, activeProject) {

    var projectApi = {
      projects: []
    };

    function getProjectList() {
      var deferred = $q.defer();
      $http
        .get('/api/project')
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

    getProjectList();

    _.assign(projectApi, {
      getProjectList: getProjectList,
      getActiveProject: function () {
        var projectId = activeProject.getProjectIdForCurrentUser();
        if (projectId) {
          return $http.get('/api/project/' + projectId);
        }
      },
      createProject: function(data) {
        return $http.post(
          '/api/project', data, {responseType:'blob'});
      },
      updateProject: function(id, data) {
        return $http.put(
          '/api/project/' + id, data, {responseType:'blob'});
      },
      deleteProject: function(id) {
        return $http.delete('/api/project/' + id);
      },
      deleteSelectedProjects: function(projects) {
        return $http({
          method: 'DELETE',
          url: '/api/project',
          data: { projects: projects}
        });
      },
      downloadSelectedProjects: function(projects) {
        return $http.post('/api/project/portfolio', { projects: projects}, {responseType:'arraybuffer'});
      },
      copyProject: function(sourceId, destinationName) {
        return $http.post('/api/project/' + sourceId + '/copy', {to: destinationName});
      },
      downloadProjectFile: function(projectId) {
        return $http.get(
          '/api/project/'+ projectId + '/data',
          {
            headers: {'Content-type': 'application/octet-stream'},
            responseType:'blob'
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
