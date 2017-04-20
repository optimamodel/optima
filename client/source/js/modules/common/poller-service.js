define(['angular' ], function (angular) {
  'use strict';

  /**
   * pollerService provide generic services to run polling tasks
   * on a URL. It expects a return JSON data structure
   * { 'status': 'started' } to continue polling, otherwise it
   * sends the response to `callback`
   */

  return angular.module('app.common.poller-service', [])

    .factory('pollerService', ['$http', '$timeout', 'utilService',
      function($http, $timeout, utilService) {

      var polls = {};

      function getPoll(id) {
        if (!(id in polls)) {
          console.log('Creating polling slot for', id);
          polls[id] = {isRunning: false, id: id};
        }
        return polls[id];
      }

      function startPoll(id, url, callback) {
        var poll = getPoll(id);
        poll.url = url;
        poll.callback = callback;

        if (!poll.isRunning) {
          console.log('Launch polling for', poll.id);
          poll.isRunning = true;

          function pollWithTimeout() {
            var poll = getPoll(id);
            $http
              .get(poll.url)
              .success(function(response) {
                if (response.status === 'started') {
                  poll.timer = $timeout(pollWithTimeout, 1000);
                } else {
                  stopPoll(id);
                }
                poll.callback(response);
              })
              .error(function(response) {
                stopPoll(id);
                poll.callback(response);
              });
          }

          pollWithTimeout();
        }
      }

      function startPollForRpc(pyobjectId, taskId, callback) {
        var poll = getPoll(taskId);
        poll.callback = callback;

        if (!poll.isRunning) {
          console.log('Launch polling for', poll.id);
          poll.isRunning = true;

          function pollWithTimeout() {
            var poll = getPoll(taskId);
            utilService
              .rpcAsyncRun(
                'check_calculation_status', [pyobjectId, taskId])
              .then(
                function(response) {
                  var status = response.data.status;
                  if (status === 'started') {
                    poll.timer = $timeout(pollWithTimeout, 1000);
                  } else {
                    stopPoll(taskId);
                  }
                  poll.callback(response);
                },
                function(response) {
                  stopPoll(taskId);
                  poll.callback(response);
                });
          }

          pollWithTimeout();
        }
      }


      function stopPoll(id) {
        var poll = getPoll(id);
        if (poll.isRunning) {
          console.log('Stop polling for', poll.id);
          poll.isRunning = false;
          $timeout.cancel(poll.timer);
        }
      }

      function stopPolls() {
        _.each(polls, function(poll) {
          if (poll.isRunning) {
            console.log('Stop polling for', poll.id);
            poll.isRunning = false;
            $timeout.cancel(poll.timer);
          }
        });
      }

      function killJob(projectId, workType) {
        $http
          .delete('/api/task/' + projectId + '/type/' + workType);
      }

      return {
        startPoll: startPoll,
        startPollForRpc: startPollForRpc,
        stopPolls: stopPolls,
        killJob: killJob
      };

    }]);

});
