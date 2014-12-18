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
      category: "Prevention",
      name: "Condom promotion and distribution", saturating: true,
      parameters: [
        {
          active: true,
          value: { 'signature': ['condom', 'reg'], 'pops': ['ALL_POPULATIONS'] }
        },
        {
          active: true,
          value: { 'signature': ['condom', 'cas'], 'pops': ['ALL_POPULATIONS'] }
        }
      ]
    },
    {
      active: false, short_name: "SBCC",
      category: "Prevention",
      name: "Social and behavior change communication", saturating: true,
      parameters: [
        {
          active: true,
          value: { 'signature': ['condom', 'reg'], 'pops': ['ALL_POPULATIONS'] }
        },
        {
          active: true,
          value: { 'signature': ['condom', 'cas'], 'pops': ['ALL_POPULATIONS'] }
        }
      ]
    },
    {
      active: false, short_name: "STI",
      category: "Prevention",
      name: "Diagnosis and treatment of sexually transmissible infections", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['stiprevdis'], 'pops': ['ALL_POPULATIONS']}
        },
        {
          active: true,
          value: {'signature': ['stiprevulc'], 'pops': ['ALL_POPULATIONS']}
        }
      ]
    },
    {
      active: false, short_name: "VMMC",
      category: "Prevention",
      name: "Voluntary medical male circumcision", saturating: false,
      parameters: [
        {
          active: true,
          value: {'signature': ['numcircum'], 'pops': ['ALL_POPULATIONS']}
        }
      ]
    },
    {
      active: false, short_name: "Cash transfers",
      category: "Prevention",
      name: "Cash transfers for HIV risk reduction", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['numacts', 'reg'], 'pops': ['ALL_POPULATIONS']}
        },
        {
          active: true,
          value: {'signature': ['numacts', 'cas'], 'pops': ['ALL_POPULATIONS']}
        }
      ]
    },
    {
      active: false, short_name: "FSW programs",
      category: "Prevention",
      name: "Programs for female sex workers and clients", saturating: true,
      parameters: [
        {
          active: true,
          value: { 'signature': ['condom', 'com'], 'pops': ['FSW'] }
        },
        {
          active: true,
          value: { 'signature': ['condom', 'com'], 'pops': ['CSW'] }
        },
        {
          active: true,
          value: { 'signature': ['hivtest'], 'pops': ['FSW'] }
        }
      ]
    },
    {
      active: false, short_name: "MSM programs",
      category: "Prevention",
      name: "Programs for men who have sex with men", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['condom', 'reg'], 'pops': ['MSM']}
        },
        {
          active: true,
          value: {'signature': ['condom', 'cas'], 'pops': ['MSM']}
        }
      ]
    },
    {
      active: false, short_name: "PWID programs",
      category: "Prevention",
      name: "Programs for people who inject drugs", saturating: true,
      parameters: [
        {
          name: 'HIV testing rates',
          active: true,
          value: {'signature': ['hivtest'], pops: ['PWID']}
        },
        {
          active: true,
          name: 'Needle-syringe sharing rates',
          value: {'signature': ['sharing'], pops: ['PWID']}
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
      category: "Prevention",
      name: "Opiate substitution therapy", saturating: false,
      parameters: [
        {
          active: true,
          value: {'signature': ['numost'], 'pops': ['ALL_POPULATIONS']}
        }
      ]

    },
    {
      active: false, short_name: "NSP",
      category: "Prevention",
      name: "Needle-syringe program", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['sharing'], 'pops': ['ALL_POPULATIONS']}
        }
      ]

    },
    {
      active: false, short_name: "PrEP",
      category: "Prevention",
      name: "Pre-exposure prophylaxis/microbicides", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['prep'], 'pops': ['ALL_POPULATIONS']}
        }
      ]

    },
    {
      active: false, short_name: "PEP",
      category: "Prevention",
      name: "Post-exposure prophylaxis", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['pep'], 'pops': ['ALL_POPULATIONS']}
        }
      ]

    },
    {
      active: false, short_name: "HTC",
      category: "Care and treatment",
      name: "HIV testing and counseling", saturating: true,
      parameters: [
        {
          active: true,
          value: {'signature': ['hivtest'], 'pops': ['ALL_POPULATIONS']}
        }
      ]

    },
    {
      active: false, short_name: "ART",
      category: "Care and treatment",
      name: "Antiretroviral therapy", saturating: false,
      parameters: [
        {
          active: true,
          value: {'signature': ['tx1'], 'pops': ['ALL_POPULATIONS']}
        },
        {
          active: true,
          value: {'signature': ['tx2'], 'pops': ['ALL_POPULATIONS']}
        }
      ]

    },
    {
      active: false, short_name: "PMTCT",
      category: "Care and treatment",
      name: "Prevention of mother-to-child transmission", saturating: false,
      parameters: [
        {
          active: true,
          value: {'signature': ['numpmtct'], 'pops': ['ALL_POPULATIONS']}
        }
      ]
    },
    {
      active: false, short_name: "Other care",
      category: "Care and treatment",
      name: "Other HIV care", saturating: false
    },
    {
      active: false, short_name: "OVC",
      category: "Care and treatment",
      name: "Orphans and vulnerable children", saturating: false
    },
    {
      active: false, short_name: "MGMT",
      category: "Management and administration",
      name: "Management", saturating: false
    },
    {
      active: false, short_name: "HR",
      category: "Management and administration",
      name: "HR and training", saturating: false
    },
    {
      active: false, short_name: "ENV",
      category: "Other",
      name: "Enabling environment", saturating: false
    },
    {
      active: false, short_name: "SP",
      category: "Other",
      name: "Social protection", saturating: false
    },
    {
      active: false, short_name: "M&E",
      category: "Management and administration",
      name: "Monitoring, evaluation, surveillance, and research", saturating: false
    },
    {
      active: false, short_name: "INFR",
      category: "Other",
      name: "Health infrastructure", saturating: false
    },
    {
      active: false, short_name: "Other",
      category: "Other",
      name: "Other costs", saturating: false
    }
  ];

  return module.constant('DEFAULT_PROGRAMS', DEFAULT_PROGRAMS)
    .constant('DEFAULT_POPULATIONS', DEFAULT_POPULATIONS);

});
