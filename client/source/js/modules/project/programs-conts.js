define(['./module'], function (module) {
  'use strict';

  return module.constant('PROGRAMS', [
    {
      name: '01 Prevention',
      acronym: '01',
      programs: [
        {
          name: 'Behavior change and communication',
          acronym: 'BCC',
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
    },
    {
      name: '03 Orphans and vulnerable children (OVC)',
      acronym: '03',
      programs: [
        {
          name: '03.01 OVC Education',
          acronym: '03.01',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.02 OVC Basic health care',
          acronym: '03.02',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.03 OVC Family/home support',
          acronym: '03.03',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.04 OVC Community support',
          acronym: '03.04',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.05 OVC Social Services and Administrative costs',
          acronym: '03.05',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.06 OVC Institutional care',
          acronym: '03.06',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.98 OVC Services not disaggregated by intervention',
          acronym: '03.98',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        },
        {
          name: '03.99 OVC services n.e.c',
          acronym: '03.99',
          indicators: [
            { name: 'Influences DALYs and may influence behaviour with older partners', active: true }
          ]
        }
      ]
    },
    {
      name: '04 Programme management and administration',
      acronym: '04',
      programs: [
        {
          name: '04.01 Planning, coordination and programme management',
          acronym: '04.01',
          indicators: [
          ]
        },
        {
          name: '04.02 Administration and transaction costs associated with managing and disbursing funds',
          acronym: '04.02',
          indicators: [
          ]
        },
        {
          name: '04.03 Monitoring and evaluation',
          acronym: '04.03',
          indicators: [
          ]
        },
        {
          name: '04.04 Operations research',
          acronym: '04.04',
          indicators: [
          ]
        },
        {
          name: '04.05 Serological-surveillance (serosurveillance)',
          acronym: '04.05',
          indicators: [
          ]
        },
        {
          name: '04.06 HIV drug-resistance surveillance',
          acronym: '04.06',
          indicators: [
          ]
        },
        {
          name: '04.07 Drug supply systems',
          acronym: '04.07',
          indicators: [
          ]
        },
        {
          name: '04.08 Information technology',
          acronym: '04.08',
          indicators: [
          ]
        },
        {
          name: '04.09 Patient tracking',
          acronym: '04.09',
          indicators: [
          ]
        },
        {
          name: '04.10 Upgrading and construction of infrastructure',
          acronym: '04.10',
          indicators: [
          ]
        },
        {
          name: '04.11 Mandatory HIV testing (not VCT)',
          acronym: '04.11',
          indicators: [
          ]
        },
        {
          name: '04.98 Programme management and administration not disaggregated by type',
          acronym: '04.98',
          indicators: [
          ]
        },
        {
          name: '04.99 Programme management and administration n.e.c',
          acronym: '04.99',
          indicators: [
          ]
        }
      ]
    },
    {
     name: '05 Human resources',
     acronym: '05',
     programs: [
       {
         name: '05.01 Monetary incentives for human resources',
         acronym: '05.01',
         indicators: []
       },
       {
         name: '05.02 Formative education to build-up an HIV workforce',
         acronym: '05.02',
         indicators: []
       },
       {
         name: '05.03 Training',
         acronym: '05.03',
         indicators: []
       },
       {
         name: '05.98 Human resources not disaggregated by type',
         acronym: '05.98',
         indicators: []
       },
       {
         name: '05.99 Human resources n.e.c.',
         acronym: '05.99',
         indicators: []
       }
     ]
   },
   {
     name: '06 Social protection and social services  (excluding OVC)',
     acronym: '06',
     programs: [
       {
         name: '06.01 Social protection through monetary benefits',
         acronym: '06.01',
         indicators: []
       },
       {
         name: '06.02 Social protection through in-kind benefits',
         acronym: '06.02',
         indicators: []
       },
       {
         name: '06.03 Social protection through provision of social services',
         acronym: '06.03',
         indicators: []
       },
       {
         name: '06.04 HIV-specific income generation projects',
         acronym: '06.04',
         indicators: []
       },
       {
         name: '06.98 Social protection services and social services not disaggregated by type',
         acronym: '06.98',
         indicators: []
       },
       {
         name: '06.99 Social protection services and social services n.e.c.',
         acronym: '06.99',
         indicators: []
       }
     ]
   },
   {
     name: '07 Enabling environment',
     acronym: '07',
     programs: [
       {
         name: '07.01 Advocacy',
         acronym: '07.01',
         indicators: []
       },
       {
         name: '07.02 Human rights programmes',
         acronym: '07.02',
         indicators: []
       },
       {
         name: '07.03 AIDS-specific institutional development',
         acronym: '07.03',
         indicators: []
       },
       {
         name: '07.04 AIDS-specific programmes focused on women',
         acronym: '07.04',
         indicators: []
       },
       {
         name: '07.05 Programmes to reduce Gender Based Violence',
         acronym: '07.05',
         indicators: []
       },
       {
         name: '07.98 Enabling environment not disaggregated by type',
         acronym: '07.98',
         indicators: []
       },
       {
         name: '07.99 Enabling environment n.e.c.',
         acronym: '07.99',
         indicators: []
       }
     ]
    },      
    {
      name: '08 HIV and AIDS-related research (excluding operations research )',
      acronym: '08',
      programs: [
       {
         name: '08.01 Biomedical research',
         acronym: '02.02.01',
         indicators: []
       },
       {
         name: '08.02 Clinical research',
         acronym: '08.02',
         indicators: []
       },
       {
         name: '08.03 Epidemiological research',
         acronym: '08.03',
         indicators: []
       },
       {
         name: '08.04 Social science research',
         acronym: '08.04',
         indicators: []
       },
       {
         name: '08.05 Vaccine-related research',
         acronym: '08.05',
         indicators: []
       },
       {
         name: '08.98 HIV and AIDS-related research activities not disaggregated by type',
         acronym: '08.98',
         indicators: []
       },
       {
         name: '08.99 HIV and AIDS-related research activities n.e.c.',
         acronym: '08.99',
         indicators: []
       },
       {
         name: '08.99.98 All other HIV activities not disaggregated by intervention and not classifiable in categories ASC.01.98 to ASC.08.98',
         acronym: '08.99.98',
         indicators: []
       },
       {
         name: '08.99.99 All other HIV activities not classifiable in categories ASC.01.99 to ASC.08.99',
         acronym: '08.99.99',
         indicators: []
       }
     ]
   }
  ]);

});
