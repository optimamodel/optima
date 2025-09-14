# Optima Changelog

Projects before `2.11.4` should be able to be migrated to version `2.11.4` without changing the calibration. Versions `2.12.0` and `2.12.1` both change the calibration (sometimes only slightly).

Versions `2.11.4`, `2.12.0` and later all can be run using the branch `main`. A project will automatically update to the earliest supported version (currently `2.11.4`), but updating a project to the latest version can be done using the FE or `op.migrate(P, 'latest')`

## Revision 12
 - `Resultset.quantile` tracks which quantiles where used to generate the results: either a list of 3 floats or `'allsamples'` which keeps all the samples.
 - `model()` takes `flattenraw` keyword to flatten the raw advancedtracking arrays to remove most of the values which are 0. `flattenraw = True` takes ~20% longer but it is more memory efficient and raw results are 80-90% smaller (`advancedtracking=True, keepraw=True`). `flattenraw = False` is the default except when running with sensitivity and advancedtracking (which would previously cause OOM errors).
     - **BREAKING CHANGE**: This only applies to `raw['incimethods'], raw['transitpopbypop']` so when those are accessed (even if `flattenraw = False`), you must call it: 
     `raw['incimethods']()` or `raw['transitpopbypop']()` which will unflatten or return the original.
 - **BREAKING CHANGE**: `raw['incionpopbypop']` has been removed as it was just a copy of `raw['incimethods']` (saves ~10% raw results size). Tt was defined as: `raw['incionpopbypop'] = raw_incionpopbypopmethods.sum(axis=0) # Removes the method of transmission`
 - `Resultset.version` and `Resultset.revision` track which version and revision were used to create the results
 - `Resultset.__add__, Resultset.__sub__` work properly (actually subtracts the values) and sames the `.parentnames` and `.operation` in the resultant Resultset
 - `Resultset.pars.func = None` now, if you want to have the `func` which checks the version of the parameters, then add the pars to a `Parameterset`. This was making some project files 10x too big if they were run in parallel.
 - `Multiresultset.rawresultsets` keeps the original Resultsets if `keepresultsetlist=True` when creating it else `None`. (Needs the Resultsets to have unique names)
 - `utils.py`: `standard_cp` and `standard_dcp` now work as originally intended (sometimes the `_dcp` would be pointing at the original object)
 - `utils.py`: `parallelpool` is a wrapper around `cf.ProcessPoolExecutor`
 - Improved `restorelinks()` for all objects
 - `Project.runsim()` takes a `parallelizer` kwarg for using a shared pool when running in parallel

## Revision 11
 - Fix `checkifparsetoverridesscenario()` not working with multiple budget years
 - Small FE fixes

## Revision 10
 - Add objective option for minimising number of prevalent undiagnosed HIV infections

## Revision 9
 - Update calculation of ICERS to be based on a minimum $1000 budget for programs so that marginal ICERs can be calculated (plus minor changes to ordering of operations)

## Revision 8
 - Update definition of "latediag" to be CD4<350 (and add separate output for undiagCD4<350 to align)

## Revision 7
 - Add most "other" outputs to the standard excel sheet with optional argument - this just adds everything that doesn't generate a hard error from a copy of the main code, so it could be improved, but these results are still useful for troubleshooting.

## Revision 6
 - Reset the fromdata attribute of the numcirc parameter (to 1.0) to allow it to be updated (older version migration did not ensure this)

## Revision 5
 - Update random number generator seeding in `runsim` by seeding a list of `default_rng` objects that are passed through to parameters that need to be sampled within each individual `makesimpars` to both ensure consistency and to avoid all parameters being sampled based on the same seed (e.g. all low or all high)
 - When sampling, each parameter will use its own generator seeded by the global seed + a hash of the parameter short name - this means that changing which parameters are sampled will still be consistent for other parameters for the same seed, resulting in more consistent outputs

## Revision 4
 - Update methods of transmission tracking (`advancedtracking=True`) so `numinciallmethods` is split by regular, casual, commercial acts. `numincimethods` remains the same.
   - This causes `advancedtracking=True` to run ~20-25% slower as there is now 8 methods of transmission instead of 4.
   - `numincimethods` now more accurately sums to `numinci` (tested to be less than 1 part in 1 million total error)
   - The intersection of multiple methods per transmission is estimated differently: instead of considering intersections as being a part of the higher probability method, all the intersections are now split according to the ratio of the method probabilities. 
 - `P.makespreadsheet()` can now take different `datastart, dataend` than the current data to extend or shrink the databook years.
 - Updated defaults `settings.now = 2023.0` and `settings.dataend = 2040.0`

## Revision 3
Fix small unpickling bug and FE raises BadFileFormatError when uploading project that it cannot unpickle.

## Revision 2
Fix bug when deep-copying a `Parameterset`, the `pars` from a different `Parameterset` would get copied in certain cases (make sure to pass `memodict` along when deep-copying).


## Revision 1
Can run multiple different supported versions with the same branch! Currently supported: `[2.11.4, 2.12.0]`

Migration to a new version is done on load `P = get_latest_project("example", migrateversion='supported')` with options of `'supported'` (default) which updates to the earliest supported version, `'minor'` which updates to the latest within the same 2.X , `'major' = 'latest' = True` which updates to the latest version, `False` which does not update (will give a big warning if the version that the project is on is not supported).
 - `P.revision` added and first migration added which:
   - Converts `P.parsets, P.progsets, parset.pars, progset.programs` into `odict_custom`s which:
   - `odict_custom` is a new class that calls a custom function `func` every time a value(s) gets set in the odict
   - In the case of `P.parsets, P.progsets, parset.pars, progset.programs`, the `odict_custom.func = checkpropagateversion` which checks the `projectversion` of the object that gets added (that it is equal) and if it doesn't have a version, then it adds it. So `Parameterset, Programset, Par, Program`  now all get `.projectversion`  added
   - They also get a `getprojectversion()` that checks that the different `projectversions` match / gets the project version from the `projectref` if need be
   - The `odict_custom.func` is `checkpropagateversion` which checks that `P.version` is changed then that gets propagated automatically 
 - If `P.version` is changed then that gets propagated automatically using `__setattr__` in `Project, Parameterset, Programset`
 - Added `projectversion or version` as a argument to many functions, which defaults to finding it itself (eg in `Par.interp`, the `Par` has `self.projectversion` which should be set automatically) eg. `model, makepars, makesimpars` which are all version-dependent functions
 - Custom `__copy__`  and `__deepcopy__` functions for objects that have `odict_custom`s to set the `odict_custom.func` to the new `object.checkpropagateversion` (the `odict_custom.func` gets set to `None` when copying)
 - `loadspreadsheet` and `makespreadsheet` have `version / projectversion` as arguments to check compatibility and make / load spreadsheet in the version-correct behaviour
 - When loading a spreadsheet, the matrices get their dimensions checked properly
 - Speed up plotting by ~30-50% (only plot actual data points not `nan` and faster way of setting axis label fontsize)
 - `runscenarios` can be run in parallel (creates a copy of the project for each scenario with only the parset and progset it needs)
 - `addblankdata` in `loadtools.py` now adds the correctly shaped blank data to `P.data` for new parameters, fixing an error downloading spreadsheets of migrated projects



## Revision 0 and earlier
 - `runsim()` now has a argument `parallel` to which, when `True`, runs the creation of simpars and the model in parallel.
 - MTCT is now attributed to PLHIV instead of susceptible states, but it is still an approximation which could be improved.
 - Emigration is split from background death in the results, meaning new results `results.other['numemi']` and `results.other['numemiplhiv']` to match immigration.
 - `__init__.py` is now structured to import the submodules without underscores eg `op.project` used to be `op._project` since pickling was throwing an error. So don't confuse `op.project` (submodule) with `op.Project` (object).
 - Outcomes optimization now stop at after a `maxtime` properly.
 - Speed-ups to both running the model and optimizations.
 - Budget and coverage scenarios need to have at least 1 year for the programs to start applying from - otherwise an error is thrown.
 - Update `numcirc` to default to "general" not "percentage" format in databooks (and to load correctly)

### FE changes
 - An error will show if making a program with the same long or short name as another one.
 - The Optimization constraints are now proportional to the default budget (latest) for that progset (`proporigconstraints`). This means a 100% min constraint actually means the min budget is the latest budget - as opposed to having to scale it up or down depending on the total budget. If an Optim also has `contraints` and `absconstraints` those will also be followed and reflected in the constraints shown. But if you change the optimization then the `constraints` and `absconstraints` will be removed.

## [2.12.3] - 
 - More memory efficient `ResultsSet.make()` function which indexes the raw arrays when assembling not after: changes results by ~1e-9
ALL PLANNED / TODO:
 - !! TB/HIV co-infection mortality
 - Change acts to be better balanced
 - Change acts to either be 0%, 50% or 100% insertive or receptive for a population, not based on the numbers in the Partnerships tab - these numbers are used to calibrate the split of a population's acts with the other populations, not the relative insertive/receptive split.
 - `Multiresultset.parsetname` and `Multiresultset.progsetname` is now an odict, with a key and value for each result.
 - Change `forcepopsize` to not affect the number of PLHIV. The previous assumption was to remove (or add) people from (or into) the susceptible and the "not on ART" states. Now people only are removed from (or added into) the susceptible states.


# [2.12.2] - 2024-07-17
 - Clean up MTCT code and fix problems:
   - MTCT of people on ART was being double-counted
   - Changed who PMTCT goes to based on their diagnosis / treatment state:
     - Previously went randomly to anyone diagnosed, including people diagnosed but not in care. This meant some pregnant people on ART were not getting PMTCT but they were getting the low probability of transmission from being on ART.
     - eg: 100 preg people on ART, 100 preg people who are dx but not on ART, data PMTCT: 100 on PMTCT -> 50 dx (not on ART people) on PMTCT, 50 people on ART also on PMTCT, 50 people on ART but not PMTCT = 150 births at the lower probability of being on PMTCT
     - Now: first give PMTCT to anyone on ART, then if there is more PMTCT spots, put any diagnosed people not on ART onto PMTCT. Then if there is more PMTCT spots, try to diagnose people to put onto PMTCT (they can go onto ART next time step if there is spots).
     - eg: 100 preg people on ART, 100 preg people who are dx but not on ART, data PMTCT: 100 on PMTCT -> *Only* 100 on ART also PMTCT = 100 births on PMTCT
     - NOTE: this can mean that populations which have more people on ART get more PMTCT if there is only enough spots for the number of people on ART
 - Fix rare negative people issue when FOI is very high (when probability of infection for a population is >1) - make FOI = min(FOI, 1)

## [2.12.1] - 2024-05-27
 - Fix `numcirc` being set to 0 in the `Parameterset` upon loading from data - meaning running with just a parset had no VMMC. Running scenarios or programs affecting `numcirc` (eg. with VMMC program) were still working, just not the calibration.
   - The migration reloads the `numcirc` in every `parset` from the `P.data` which is from the latest loaded spreadsheet (for the parsets that have `numcirc.y = 0`).


## [2.12.0] - 2023-
New changes - most of these change the calibration (some only slightly):

|       | M   | F   | MSM1 | MSM2 | TGW |
|-------|-----|-----|------|------|-----|
| M     |     | 1   |      |      | 1   |
| F     |     |     |      |      |     |
| MSM1  |     | 1   | 10   | 5    | 1   |
| MSM2  |     |     | 1    | 1    | 1   |
| TGW   |     |     |      |      |     |

 - Sexual partnerships are now properly direction - in the Partnerships tab insertive is on the left, receptive on top - example above.
eg.
   - This means TGW receive the proper (higher) risk associated with only having receptive acts.
   - If there are multiple MSM populations which both have both receptive and insertive risk then there should be a number in both spots in the matrix. The insertive acts will be split proportionally to the numbers in each spot. eg. in this case MSM2 has 5 receptive acts with MSM1 for every 1 insertive act.
     - (Note this was changed in `2.12.1` to be always 50/50 insertive/receptive if there is a non-zero entry in each spot).
   - If one population is M and the other F, then the acts will always be insertive for the M population and receptive for the F, regardless of the direction in the databook.
   - Note that an old project will keep the old acts behaviour until it is updated from a databook on `>2.12.0`
   - Behind the scenes, the `pars['actsreg']` etc, now only stores the insertive acts, and is "per insertive population" so the calculation of the corresponding receptive acts happens during creation of the `simpars['actsreginsertive']` and `simpars['actsregreceptive']` etc which the model uses. `pars['actsreg'].insertiveonly = True` etc is for the new behaviour, a migration means older projects are `False` until updated from a databook.
- Condom use now properly stored only once per partnership in the parset, preferring (M,F) and sorting (M,M) partnerships alphabetically. This means programs only need to target condom use for (MSM1, MSM2) not also (MSM2, MSM1)
- ANC testing for HIV+ mothers happens automatically based on the number of mothers on PMTCT - if there are not enough diagnosed HIV+ pregnant mothers, then a proportion of each population's undiagnosed HIV+ pregnant women will be diagnosed to fill the `numpmtct` (or based on `proppmtct`).
- Only PLHIV who have been diagnosed get pregnant and give birth at the reduced rate `relhivbirth`, whereas previously it was for all PLHIV.
- `proppmtct` is now the proportion of HIV+ pregnant women who are on PMTCT, whereas the model used to interpret it as the proportion of diagnosed HIV+ mothers who are on PMTCT.
- Fixed bug where if getting population size for only one timestep, then the exponential curve would be inappropriately applied. Most noticeable in the Cost-Coverage plots in the FE.
- Other small bug fixes in the model while also speeding it up (like popsize for a single timestep - which affected Cost-Cov graphs, and a small number of people ageing two steps at once)

