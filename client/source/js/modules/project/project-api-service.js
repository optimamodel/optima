define(['./module'], function (module) {
  'use strict';

  module.factory('projectApiService', [ '$http', 'activeProject',

    function ($http, activeProject) {

      return {
        getActiveProject: function () {
          var projectId = activeProject.getProjectIdForCurrentUser();
          if (projectId) {
            return $http.get('/api/project/' + projectId);
          }
        },
        createProject: function(data) {
          return $http.post('/api/project', data, {
          responseType:'blob'});
        },
        updateProject: function(id, data) {
          return $http.put('/api/project/' + id, data, {
          responseType:'blob'});
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
        exportProject: function(data) {
          return $http.post('/api/project/export', data);
        },
        exportAllProject: function(data) {
          return $http.post('/api/project/exportall', data);
        },
        getProjectData: function(id) {
          return $http.get('/api/project/'+ id + '/data',
            {headers: {'Content-type': 'application/octet-stream'},
          responseType:'blob'});
        },
        getEconomicsData: function(id) {
          return $http.get('/api/project/'+ id + '/economics',
            {headers: {'Content-type': 'application/octet-stream'},
          responseType:'blob'});
        },
        getProjectList: function () {
          return $http.get('/api/project');
        },
        getAllProjectList: function () {
          return $http.get('/api/project/all');
        },
        getPopulations: function () {
          return $http.get('/api/project/populations');
        },
        getDefault: function (projectId) {
          return $http.get('/api/project/' + projectId + '/defaults');
        },
        getSpreadsheetUrl: function(id) {
          return '/api/project/' + id + '/spreadsheet';
        },
        getEconomicsUrl: function(id) {
          return '/api/project/' + id + '/economics';
        },
        getDataUploadUrl: function(id) {
          return '/api/project/' + id + '/data';
        }
      };

    }]);
});
