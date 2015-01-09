define([
    'angular'
], function (angular) {
    'use strict';

    return angular.module('app.common.graph-type',[])
    .factory('graphTypeFactory', ['CONFIG', function (CONFIG) {
            return {
                types: angular.copy(CONFIG.GRAPH_TYPES)
            }
    }])
});