/**
 * Defines constants for application
 */
define(['angular'], function (angular) {
  'use strict';
  return angular.module('app.constants', [])
    .constant('CONFIG', {
      GRAPH_MARGINS: {
        top: 20,
        right: 20,
        bottom: 45,
        left: 70
      },
      GRAPH_TYPES: {
        plotUncertainties: false,
        population: [
          { id: 'prev', name: 'HIV prevalence', byPopulation: true, total: false},
          { id: 'plhiv', name:'Number of PLHIV', byPopulation:false, total:true, stacked: true},
          { id: 'daly', name: 'HIV-related DALYs', byPopulation: false, total: true, stacked: true },
          { id: 'death', name: 'AIDS-related deaths', byPopulation: false, total: true, stacked: true },
          { id: 'inci', name: 'New HIV infections', byPopulation: false, total: true, stacked: true },
          { id: 'dx', name: 'New HIV diagnoses', byPopulation: false, total: true, stacked: true },
          { id: 'tx1', name: 'People on 1st-line treatment', byPopulation: false, total: true, stacked: true },
          { id: 'tx2', name: 'People on 2nd-line treatment', byPopulation: false, total: true, stacked: true }
        ],
        costs:[
          {id:"annual", name: "Annual costs"},
          {id:"cumulative",name: "Cumulative costs"}
        ],
        financial: [
          { id: 'before', name: 'People affected before 2015'},
          { id: 'after', name: 'People affected after 2015'},
          { id: 'totalplhiv', name: 'Total PLHIV'},
          { id: 'stacked', name: 'Stacked' }
        ],
        financialAnnualCosts: [
          {id:'total', name:'Total amount', disabled: true},
          {id:'gdp', name:'Proportion of GDP', disabled: true},
          {id:'revenue', name:'Proportion of government revenue', disabled: true},
          {id:'govtexpend', name:'Proportion of government expenditure', disabled: true},
          {id:'totalhealth', name:'Proportion of total health expenditure', disabled: true},
          {id:'domestichealth', name:'Proportion of domestic health expenditure', disabled: true}
        ],
        annualCost: 'total'
      }
    });
});
