# Optima Changelog

Projects before `2.11.4` should be able to be migrated to version `2.11.4` without changing the calibration. Versions `2.12.0` and `2.12.1` both change the calibration (sometimes only slightly).

Versions `2.11.4` and later all can be run using the branch `EECA-training-2022` (currently on `2.11.4`) or `updates-june-2022` (currently on `2.12.0`). These branches have the same code except for `version.py` which changes the behaviour.
To use a different version, change it without committing in `optima/version.py`.


## Changes that apply to __all__ versions since 2.11.4
 - `runsim()` now has a argument `parallel` to which, when `True`, runs the creation of simpars and the model in parallel.
 - MTCT is now attributed to PLHIV instead of susceptible states, but it is still an approximation which could be improved.
 - Emigration is split from background death in the results, meaning new results `results.other['numemi']` and `results.other['numemiplhiv']` to match immigration.
 - `__init__.py` is now structured to import the submodules without underscores eg `op.project` instead of `op._project` since pickling was throwing an error. So don't confuse `op.project` (submodule) with `op.Project` (object).
 - Outcomes optimization now stop at after a `maxtime` properly.
 - Speed-ups to both running the model and optimizations.
 - Budget and coverage scenarios need to have at least 1 year for the programs to start applying from - otherwise an error is thrown.
 - 

### FE changes
 - An error will show if making a program with the same long or short name as another one.
 - The Optimization constraints are now proportional to the default budget (latest) for that progset (`proporigconstraints`). This means a 100% min constraint actually means the min budget is the latest budget - as opposed to having to scale it up or down depending on the total budget. If an Optim also has `contraints` and `absconstraints` those will also be followed and reflected in the constraints shown. But if you change the optimization then the `constraints` and `absconstraints` will be removed.
 -


## [2.12.1] - 2023-
ALL TODO:
 - Change acts to either be 0%, 50% or 100% insertive or receptive for a population, not based on the numbers in the Partnerships tab - these numbers are used to calibrate the split of a population's acts with the other populations, not the relative insertive/receptive split.
 - Change `fixpopsize` to not affect the number of PLHIV. The previous assumption was to remove (or add) people from (or into) the susceptible and the "not on ART" states. Now people only are removed from (or added into) the susceptible states.
 - `Multiresultset.parsetname` and `Multiresultset.progsetname` is now a dictionary, with a key and value for each result.


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
- Other small bug fixes in the model while also speeding it up

