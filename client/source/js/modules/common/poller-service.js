define(['angular' ], function (angular) {
  'use strict';

  /**
   * pollerService provide generic services to run polling tasks
   * on a URL. It expects a return JSON data structure
   * { 'status': 'started' } to continue polling, otherwise it
   * sends the response to `callback`
   */

  return angular.module('app.common.poller-service', [])

    .factory('pollerService', ['$timeout', 'utilService', function($timeout, utilService) {

      var polls = {};

      function getPoll(id) {
        if (!(id in polls)) {
          console.log('Creating polling slot for', id);
          polls[id] = {isRunning: false, id: id};
        }
        return polls[id];
      }

      function startPollForRpc(pyobjectId, taskId, callback) {
        var pollId = pyobjectId + ":" + taskId;
        var poll = getPoll(pollId);
        poll.callback = callback;

        console.log('startPollForRpc checking', poll.id);

        if (!poll.isRunning) {
          console.log('startPollForRpc launch', poll.id);
          poll.isRunning = true;

          function pollWithTimeout() {
            var poll = getPoll(pollId);
            utilService
              .rpcAsyncRun(
                'check_calculation_status', [pyobjectId, taskId])
              .then(
                function(response) {
                  var status = response.data.status;
                  if (status === 'started') {
                    poll.timer = $timeout(pollWithTimeout, 1000);
                  } else {
                    stopPoll(pollId);
                  }
                  poll.callback(response);
                },
                function(response) {
                  stopPoll(pollId);
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

      return {
        startPollForRpc: startPollForRpc,
        stopPolls: stopPolls,
      };

    }]);

});
