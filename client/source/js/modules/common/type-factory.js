define([
    'angular'
], function (angular) {
    'use strict';

    return angular.module('app.common.type',[])
    .factory('typeFactory', ['CONFIG', function (CONFIG) {
            return {
                types: angular.copy(CONFIG.GRAPH_TYPES)
            }
    }])
});