define(['./module'], function (module) {
  'use strict';

  var DEFAULT_POPULATIONS = [
    {
      active: false, short_name: "FSW", name: "Female sex workers",
      sexmen: true, sexwomen: false, injects: false, sexworker: true, client: false, female: true, male: false
    },
    {
      active: false, short_name: "Clients", name: "Clients of sex workers",
      sexmen: false, sexwomen: true, injects: false, sexworker: false, client: true, female: false, male: true
    },
    {
      active: false, short_name: "MSM", name: "Men who have sex with men",
      sexmen: true, sexwomen: false, injects: false, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, short_name: "Transgender", name: "Transgender individuals",
      sexmen: true, sexwomen: false, injects: false, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, short_name: "PWID", name: "People who inject drugs",
      sexmen: true, sexwomen: false, injects: true, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, short_name: "MWID", name: "Males who inject drugs",
      sexmen: true, sexwomen: false, injects: true, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, short_name: "FWID", name: "Females who inject drugs",
      sexmen: false, sexwomen: true, injects: true, sexworker: false, client: false, female: true, male: false
    },
    {
      active: false, short_name: "Children", name: "Children (2-15)",
      sexmen: false, sexwomen: false, injects: false, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, short_name: "Infants", name: "Infants (0-2)",
      sexmen: false, sexwomen: false, injects: false, sexworker: false, client: false, female: false, male: false
    },
    {
      active: false, short_name: "Males 15-49", name: "Other males (15-49)",
      sexmen: false, sexwomen: true, injects: false, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, short_name: "Females 15-49", name: "Other females (15-49)",
      sexmen: true, sexwomen: false, injects: false, sexworker: false, client: false, female: true, male: false
    },
    {
      active: false, short_name: "Other males", name: "Other males [enter age]",
      sexmen: false, sexwomen: true, injects: false, sexworker: false, client: false, female: false, male: true
    },
    {
      active: false, short_name: "Other females", name: "Other females [enter age]",
      sexmen: true, sexwomen: false, injects: false, sexworker: false, client: false, female: true, male: false
    }
  ];

  var DEFAULT_PROGRAMS = [
    {
      active: false, short_name: "Condoms",
      name: "Condom promotion and distribution", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: { 'signature': ['condom', 'reg'], 'pops': [] }
        },
        {
          active: true,
          name: ' Condom usage probability, casual partnerships',
          value: { 'signature': ['condom', 'cas'], 'pops': [] }
        }
      ]
    },
    {
      active: false, short_name: "SBCC",
      name: "Social and behavior change communication", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: { 'signature': ['condom', 'reg'], 'pops': [] }
        },
        {
          active: true,
          name: ' Condom usage probability, casual partnerships',
          value: { 'signature': ['condom', 'cas'], 'pops': [] }
        }
      ]
    },
    {
      active: false, short_name: "STI",
      name: "Diagnosis and treatment of sexually transmissible infections", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Discharging STI prevalence',
          value: {'signature': ['stiprevdis'], 'pops': []}
        },
        {
          active: true,
          name: 'Ulcerative STI prevalence',
          value: {'signature': ['stiprevulc'], 'pops': []}
        }
      ]
    },
    {
      active: false, short_name: "VMMC",
      name: "Voluntary medical male circumcision", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of circumcisions performed per year',
          value: {'signature': ['numcircum'], 'pops': []}
        }
      ]
    },
    {
      active: false, short_name: "Cash transfers",
      name: "Cash transfers for HIV risk reduction", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Number of acts per person per year, regular',
          value: {'signature': ['numacts', 'reg'], 'pops': []}
        },
        {
          active: true,
          name: 'Number of acts per person per year, casual',
          value: {'signature': ['numacts', 'cas'], 'pops': []}
        }
      ]
    },
    {
      active: false, short_name: "FSW programs",
      name: "Programs for female sex workers and clients", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, commercial partnerships',
          value: { 'signature': ['condom', 'com'], 'pops': ['FSW'] }
        },
        {
          active: true,
          name: 'Condom usage probability, commercial partnerships',
          value: { 'signature': ['condom', 'com'], 'pops': ['CSW'] }
        },
        {
          active: true,
          name: 'HIV testing rates',
          value: { 'signature': ['hivtest'], 'pops': ['FSW'] }
        }
      ]
    },
    {
      active: false, short_name: "MSM programs",
      name: "Programs for men who have sex with men", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: {'signature': ['condom', 'reg'], 'pops': ['MSM']}
        },
        {
          active: true,
          name: 'Condom usage probability, casual partnerships',
          value: {'signature': ['condom', 'cas'], 'pops': ['MSM']}
        }
      ]
    },
    {
      active: false, short_name: "PWID programs",
      name: "Programs for people who inject drugs", saturating: true,
      parameters: [
        {
          active: true,
          name: 'HIV testing rates',
          value: {'signature': ['hivtest'], pops: ['PWID']}
        },
        {
          active: true,
          name: 'Needle-syringe sharing rates',
          value: {'signature': ['sharing'], pops: []}
        },
        {
          active: true,
          name: 'Condom usage probability, regular partnerships',
          value: {'signature': ['condom', 'reg'], pops: ['PWID']}
        },
        {
          active: true,
          name: 'Condom usage probability, casual partnerships',
          value: {'signature': ['condom', 'cas'], pops: ['PWID']}
        }
      ]

    },
    {
      active: false, short_name: "OST",
      name: "Opiate substitution therapy", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of people on OST',
          value: {'signature': ['numost'], 'pops': []}
        }
      ]

    },
    {
      active: false, short_name: "NSP",
      name: "Needle-syringe program", saturating: true,
      parameters: [
        {
          active: true,
          name: 'Needle-syringe sharing rate',
          value: {'signature': ['sharing'], 'pops': []}
        }
      ]

    },
    {
      active: false, short_name: "PrEP",
      name: "Pre-exposure prophylaxis/microbicides", saturating: true,
      parameters: [
        {
          active: true,
          name: 'PrEP prevalence',
          value: {'signature': ['prep'], 'pops': []}
        }
      ]

    },
    {
      active: false, short_name: "PEP",
      name: "Post-exposure prophylaxis", saturating: true,
      parameters: [
        {
          active: true,
          name: 'PEP prevalence',
          value: {'signature': ['pep'], 'pops': []}
        }
      ]

    },
    {
      active: false, short_name: "HTC",
      name: "HIV testing and counseling", saturating: true,
      parameters: [
        {
          active: true,
          name: 'HIV testing rates',
          value: {'signature': ['hivtest'], 'pops': []}
        }
      ]

    },
    {
      active: false, short_name: "ART",
      name: "Antiretroviral therapy", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of people on 1st-line treatment',
          value: {'signature': ['tx1'], 'pops': []}
        },
        {
          active: true,
          name: 'Number of people on 2nd-line treatment',
          value: {'signature': ['tx2'], 'pops': []}
        }
      ]

    },
    {
      active: false, short_name: "PMTCT",
      name: "Prevention of mother-to-child transmission", saturating: false,
      parameters: [
        {
          active: true,
          name: 'Number of women on PMTCT',
          value: {'signature': ['numpmtct'], 'pops': []}
        }
      ]
    },
    {
      active: false, short_name: "Other care",
      name: "Other HIV care", saturating: false
    },
    {
      active: false, short_name: "OVC",
      name: "Orphans and vulnerable children", saturating: false
    },
    {
      active: false, short_name: "MGMT",
      name: "Management", saturating: false
    },
    {
      active: false, short_name: "HR",
      name: "HR and training", saturating: false
    },
    {
      active: false, short_name: "ENV",
      name: "Enabling environment", saturating: false
    },
    {
      active: false, short_name: "SP",
      name: "Social protection", saturating: false
    },
    {
      active: false, short_name: "M&E",
      name: "Monitoring, evaluation, surveillance, and research", saturating: false
    },
    {
      active: false, short_name: "INFR",
      name: "Health infrastructure", saturating: false
    },
    {
      active: false, short_name: "Other",
      name: "Other costs", saturating: false
    }
  ];

  return module.constant('DEFAULT_PROGRAMS', DEFAULT_PROGRAMS)
    .constant('DEFAULT_POPULATIONS', DEFAULT_POPULATIONS);

});
