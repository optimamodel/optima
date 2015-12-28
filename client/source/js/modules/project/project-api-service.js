define(['./module'], function (module) {
  'use strict';

  module.factory('projectApiService', [ '$http', 'activeProject',

    function ($http, activeProject) {

      return {
        getActiveProject: function () {
          var projectId = activeProject.getProjectIdForCurrentUser();
          return $http.get('/api/project/' + projectId);
        },
        createProject: function(data) {
          return $http.post('/api/project', data);
        },
        updateProject: function(id, data) {
          return $http.put('/api/project/' + id, data);
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
          return $http.post('/api/project/' + sourceId + '/copy' + '?to=' + destinationName)
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
        getProjectList: function () {
          return $http.get('/api/project');
        },
        getAllProjectList: function () {
          return $http.get('/api/project/all');
        },
        getPredefined: function () {
          return $http.get('/api/project/predefined');
        },
        getParameters: function () {
          return $http.get('/api/project/parameters');
        },
        getSpreadsheetUrl: function(id) {
          return '/api/project/' + id + '/spreadsheet';
        },
        getDataUploadUrl: function(id) {
          return '/api/project/' + id + '/data';
        }
      };

    }]);
});
