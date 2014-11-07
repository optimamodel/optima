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
        },
        {
          name: '01.03 Voluntary counselling and testing (VCT)',
          acronym: '01.03',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.04 Risk-reduction for vulnerable and accessible populations',
          acronym: '01.04',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.05 Prevention – youth in school',
          acronym: '01.05',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.06 Prevention – youth out-of-school',
          acronym: '01.06',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.07 Prevention of HIV transmission aimed at people living with HIV (PLHIV)',
          acronym: '01.07',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.08 Prevention programmes for sex workers and their clients',
          acronym: '01.08',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.09 Programmes for men who have sex with men (MSM)',
          acronym: '01.09',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.10 Harm-reduction programmes for people who inject drugs (PWID)',
          acronym: '01.10',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.11 Prevention programmes in the workplace',
          acronym: '01.11',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.12 Condom social marketing',
          acronym: '01.12',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.13 Public and commercial sector male condom provision',
          acronym: '01.13',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.14 Public and commercial sector female condom provision',
          acronym: '01.14',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.15 Microbicides',
          acronym: '01.15',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.16 Prevention, diagnosis and treatment of sexually transmitted infections (STI)',
          acronym: '01.16',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.17 Prevention of mother-to-child transmission (PMTCT)',
          acronym: '01.17',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.18 Male circumcision',
          acronym: '01.18',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.19 Blood safety',
          acronym: '01.19',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.20 Safe medical injections',
          acronym: '01.20',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.21 Universal precautions',
          acronym: '01.21',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },
        {
          name: '01.22 Post-exposure prophylaxis (PEP)',
          acronym: '01.22',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },        
        {
          name: 'Pre-Exposure prophylaxis (PrEP)',
          acronym: 'PrEP',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },        
        {
          name: '01.98 Prevention activities not disaggregated by intervention',
          acronym: '01.98',
          indicators: [
            { name: 'Relative increase in condom use and testing in general populations', active: false },
            { name: 'VMMC uptake and ART adherence', active: true },
            { name: 'Uptake of other programs and services', active: true },
            { name: 'Linkages to biomedical services', active: false }
          ]
        },        
        {
          name: '01.99 Prevention activities n.e.c.',
          acronym: '01.99',
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
        },
        {
          name: '02.01.02 Opportunistic infection (OI) outpatient prophylaxis and treatment',
          acronym: '02.01.02',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.03 Antiretroviral therapy',
          acronym: '02.01.03',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.04 Nutritional support associated to ARV therapy',
          acronym: '02.01.04',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.05 Specific HIV-related  laboratory monitoring',
          acronym: '02.01.05',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.06 Dental programmes for PLHIV',
          acronym: '02.01.06',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.07 Psychological treatment and support services',
          acronym: '02.01.07',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.08 Outpatient palliative care',
          acronym: '02.01.08',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.09 Home-based care',
          acronym: '02.01.09',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.10 Traditional medicine and informal care and treatment services',
          acronym: '02.01.10',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.98 Outpatient care services not disaggregated by intervention',
          acronym: '02.01.98',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
        {
          name: '02.01.99 Outpatient care services n.e.c.',
          acronym: '02.01.99',
          indicators: [
            {
              name: 'Testing rates in all populations (This will be listed under care and treatment in future)',
              active: true
            }
          ]
        },
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
        },
        {
          name: '02.02.02 Inpatient palliative care',
          acronym: '02.02.02',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        },
        {
          name: '02.02.98 Inpatient care services not disaggregated by intervention',
          acronym: '02.02.98',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        },
        {
          name: '02.02.99 Inpatient care services n.e.c.',
          acronym: '02.02.99',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        },
        {
          name: '02.03 Patient transport and emergency rescue',
          acronym: '02.03',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        },
        {
          name: '02.98 Care and treatment services not disaggregated by intervention',
          acronym: '02.98',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        },
        {
          name: '02.99 Care and treatment services n.e.c.',
          acronym: '02.99',
          indicators: [
            { name: 'Informs Optima HIV expenditure unit costs for PLHIV with CD4<200', active: true }
          ]
        }
      ]
    }
  ]);

});
