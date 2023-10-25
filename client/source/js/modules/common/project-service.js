define(['angular', '../common/local-storage-polyfill'], function (angular) {
  'use strict';

  var module = angular.module('app.project-service', []);

  /**
   * projectService - a module to fetch/manipulate projects with
   * the web-server. It also provides a singleton reference
   * to existing projects and the selected project, for access
   * across all page sin the client.
   *
   * This wraps around rpc calls, as there is the global lists of
   * projects, and active states needs to be maintained w.r.t.
   * to the projects and active selected projects. As well, this
   * is to maintain some legacy code within the code-base.
   *
   * Internally, all angular http calls are implemented as $q
   * promises, and so the projectService is implemented as a $q
   * promises library, by wrapping another promise around the
   * the $http promises, so that it maintains the same interface.
   */

  module.service('projectService',
    ['$http', '$q', 'userManager', 'rpcService', function ($http, $q, userManager, rpcService) {

    var projectService = {
      projects: [],
      optimademoprojects: [],
      project: {},
      calibrationOK: false,
      programsOK: false,
      costFuncsOK: false
    };

    function makeUserKey(userId) {
      return 'activeProjectFor:' + userId;
    }

    function makeUserSettingsKey(userId) {
      return 'settingsForUser:' + userId;
    }

    function setActiveProjectId(projectId) {
      projectService.project.id = projectId;
      var projectStr = JSON.stringify(projectService.project);
      localStorage[makeUserKey(userManager.user.id)] = projectStr;
    }

    function setGraphSettings(settings) {
        var settingsStr = JSON.stringify(settings);
        localStorage[makeUserSettingsKey(userManager.user.id)] = settingsStr;
    }

    function getGraphSettings() {
        var settingsStr = localStorage[makeUserSettingsKey(userManager.user.id)];
        if (settingsStr == null || settingsStr == undefined) {
          return {'figwidth':0.48, 'fontsize':0.8}
        }
        try {
          return JSON.parse(settingsStr);
        } catch (exception) {
          return {'figwidth':0.48, 'fontsize':0.8}
        }
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
      rpcService
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
            projectService.calibrationOK = uploadedProject.calibrationOK;
            projectService.programsOK = uploadedProject.programsOK;
            projectService.costFuncsOK = uploadedProject.costFuncsOK;
            deferred.resolve(response);
          },
          function(response) {
            deferred.reject(response);
          });
      getProjectList(); // Refresh the project list after we create a new project
      return deferred.promise;
    }

    function getProjectList() {
      var deferred = $q.defer();
      rpcService
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

    function getOptimaDemoProjectList() {
      var deferred = $q.defer();
      rpcService
        .rpcRun(
          'get_optimademo_projects')
        .then(
          function(response) {
            clearList(projectService.optimademoprojects);
            _.each(response.data.projects, function(project) {
              project.creationTime = Date.parse(project.creationTime);
              project.updatedTime = Date.parse(project.updatedTime);
              project.dataUploadTime = Date.parse(project.dataUploadTime);
              projectService.optimademoprojects.push(project);
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
      rpcService
        .rpcRun('create_project', [userManager.user.id, project])
        .then(
          function(response) {
            getProjectAndMakeActive(response.data.projectId);
            rpcService
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
      rpcService
        .rpcUpload(
          'create_project_from_prj_file',
          [userManager.user.id, otherNames], 
		  {},
		  '.prj')
        .then(
          function(response) {
			if (response.data.projectId == 'BadFileFormatError') {
			  deferred.reject(response);
			} else {
              getProjectAndMakeActive(response.data.projectId)
                .then(
                  function(response) { deferred.resolve(response); },
                  function(response) { deferred.reject(response); });
			}
          },
          function(response) {
            deferred.reject(response);
          });
      return deferred.promise;
    }

    function uploadProjectFromSpreadsheet() {
      var deferred = $q.defer();
      var otherNames = _.pluck(projectService.projects, 'name');
      rpcService
        .rpcUpload(
          'create_project_from_spreadsheet',
          [userManager.user.id, otherNames], 
		  {},
		  '.xlsx')
        .then(
          function(response) {
			if (response.data.projectId == 'BadFileFormatError') {
			  deferred.reject(response);
            } else {			  
              getProjectAndMakeActive(response.data.projectId)
                .then(
                  function(response) { deferred.resolve(response); },
                  function(response) { deferred.reject(response); });
			}
          },
          function(response) {
            deferred.reject(response);
          });
      return deferred.promise;
    }

    function copyProject(projectId, newName) {
      var deferred = $q.defer();
      rpcService
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

    function copyOptimaDemoProject(projectId, newName) {
      var deferred = $q.defer();
      rpcService
        .rpcRun(
          'copy_optimademo_project', [projectId, newName])
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
      rpcService
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

    function updateProjectVersion(project) {
      var deferred = $q.defer();
      rpcService
        .rpcRun('update_project_version', [project.id])
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
      rpcService
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
//      getOptimaDemoProjectList();

      function getActiveProject() {
        var projectId = projectService.project.id;
        if (projectId) {
          return getProjectAndMakeActive(projectId)
        }
      }

    _.assign(projectService, {
      getProjectList: getProjectList,
      getOptimaDemoProjectList: getOptimaDemoProjectList,
      setActiveProjectId: setActiveProjectId,
      loadActiveProject: loadActiveProject,
      clearProjectIdIfActive: clearProjectIdIfActive,
      clearProjectForUserId: clearProjectForUserId,
      isActiveProjectSet: isActiveProjectSet,
      copyProject: copyProject,
      copyOptimaDemoProject: copyOptimaDemoProject,
      renameProject: renameProject,
      createProject: createProject,
      deleteProjects: deleteProjects,
      uploadProject: uploadProject,
      uploadProjectFromSpreadsheet: uploadProjectFromSpreadsheet,
      getActiveProject: getActiveProject,
      setGraphSettings: setGraphSettings,
      getGraphSettings: getGraphSettings,
      updateProjectVersion: updateProjectVersion,
      downloadSelectedProjects: function (projectIds) {
        return rpcService.rpcDownload('load_zip_of_prj_files', [projectIds]);
      },
      getAllProjectList: function () {
        return rpcService.rpcRun('load_all_project_summaries');
      },
      getPopulations: function () {
        return rpcService.rpcRun('get_default_populations');
      },
      getDefaultPrograms: function (projectId) {
        return rpcService.rpcRun('load_project_program_summaries', [projectId]);
      },
    });

    return projectService;

  }]);
});
