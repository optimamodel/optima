define(['angular' ], function (angular) {
  'use strict';

  /**
   * pollerService provide generic services to run polling tasks
   * on async celery tasks on the webserver.
   *
   * It interacts with the Postgres db on the WorkLogDb table.
   * Every task is given a taskId, and the poller returns a
   * calc_state dictionary, where the key property is `status`.
   * A return value of { 'status': 'started' } is used to continue
   * polling, otherwise it sends the response to `callback`
   *
   * A page may query multiple polls.
   *
   * When a new page is opened, it is useful to close all running
   * polls from older pages.
   *
   */

  return angular.module('app.poller-service', [])

    .factory('pollerService', ['$timeout', 'rpcService', function($timeout, rpcService) {

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
            rpcService
              .rpcAsyncRun(
                'check_task', [taskId])
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
