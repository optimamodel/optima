import optima


def parse_portfolio_summaries(portfolio):
    gaoptim_summaries = []
    objectivesList = []
    for gaoptim_key, gaoptim in portfolio.gaoptims.items():
        resultpairs_summary = []
        for resultpair_key, resultpair in gaoptim.resultpairs.items():
            resultpair_summary = {}
            for result_key, result in resultpair.items():
                result_summary = {
                    'name': result.name,
                    'id': result.uid,
                }
                resultpair_summary[result_key] = result_summary
            resultpairs_summary.append(resultpair_summary)

        gaoptim_summaries.append({
            "key": gaoptim_key,
            "objectives": dict(gaoptim.objectives),
            "id": gaoptim.uid,
            "name": gaoptim.name,
            "resultpairs": resultpairs_summary
        })

        objectivesList.append(gaoptim.objectives)

    project_summaries = []

    for project in portfolio.projects.values():
        boc = project.getBOC(objectivesList[0])
        project_summary = {
            'name': project.name,
            'id': project.uid,
            'boc': 'calculated' if boc is not None else 'not ready',
            'results': []
        }
        for result in project.results.values():
            project_summary['results'].append({
                'name': result.name,
                'id': result.uid
            })
        project_summaries.append(project_summary)

    result = {
        "created": portfolio.created,
        "name": portfolio.name,
        "gaoptims": gaoptim_summaries,
        "id": portfolio.uid,
        "version": portfolio.version,
        "gitversion": portfolio.gitversion,
        # "outputstring": portfolio.outputstring,
        "projects": project_summaries,
    }
    return result

import pprint

portfolio = optima.loadobj("example/malawi-decent-two-state.prt", verbose=0)
pprint.pprint(parse_portfolio_summaries(portfolio))

with open('portfolio.csv', 'w') as f:
    f.write(portfolio.outputstring.replace('\t', ','))

