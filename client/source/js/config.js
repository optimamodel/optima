/**
 * Defines constants for application
 */
define(['angular'], function (angular) {
  'use strict';
  return angular.module('app.constants', [])
    .constant('CONFIG', {
      GRAPH_TYPES: [
        { id: 'prev', name: 'Prevalence', active: true, byPopulation: true, total: false },
        { id: 'daly', name: 'DALYs', active: false, byPopulation: false, total: true },
        { id: 'death', name: 'Deaths', active: false, byPopulation: false, total: true },
        { id: 'inci', name: 'New infections', active: false, byPopulation: false, total: true },
        { id: 'dx', name: 'Diagnoses', active: false, byPopulation: false, total: true },
        { id: 'tx1', name: 'First-line treatment', active: false, byPopulation: false, total: true },
        { id: 'tx2', name: 'Second-line treatment', active: false, byPopulation: false, total: true }
      ]
    });
});
