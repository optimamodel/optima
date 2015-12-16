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
        },
        getProjectProgramSet: function(id) {
          return $http.get('/api/project/' + id + '/progsets' );
        },
        saveProjectProgramSet: function(projectId, progSetId, data) {
          return $http({
            url: '/api/project/' + projectId + '/progsets' + (progSetId ? '/' + progSetId : ''),
            method: (progSetId ? 'PUT' : 'POST'),
            data: data
          });
        },
        deleteProjectProgramSet: function(projectId, progSetId) {
          return $http.delete('/api/project/' + projectId +  '/progsets' + '/' + progSetId);
        }
      };

    }]);
});
