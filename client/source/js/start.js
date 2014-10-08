// obtain requirejs config
require(['require', './js/config-require'], function (require, config) {

  // set cache beater
  config.urlArgs = 'bust=v0.4.0';

  // update global require config
  window.require.config(config);

  // load app
  require(['./js/main.js']);
});
