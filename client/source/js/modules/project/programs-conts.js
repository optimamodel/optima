define(['./module'], function (module) {
  'use strict';

  return module.constant('PROGRAMS', [
    {
      name: '01 Prevention',
      acronym: '01',
      programs: [
        {
          name: '01.01 Communication for social and behavioural change',
          acronym: '01.01',
          indicators: [
            { name: 'Condom use among general population males and females', active: true },
            { name: 'VMMC uptake and ART adherence', active: false },
            { name: 'Uptake of other programs and services', active: false },
            { name: 'Linkages to biomedical services', active: true }
          ]
        },
        {
          name: '01.02 Community mobilization',
          acronym: '01.02',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        }
      ]
    },
    {
      name: '02.01 Care and treatment - Outpatient care',
      acronym: '02.01',
      programs: [
        {
          name: '02.01.01 Provider- initiated testing and counselling (PITC)',
          acronym: '02.01.01',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        }
      ]
    },
    {
      name: '02.02 Care and treatment - Inpatient care',
      acronym: '02.02',
      programs: [
        {
          name: '02.02.01 Inpatient treatment of opportunistic infections (OI)',
          acronym: '02.02.01',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        }
      ]
    }
  ]);

});
