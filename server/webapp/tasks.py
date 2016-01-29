from server.celery_app import make_celery

from server.api import app


celery = make_celery(app)


@celery.task()
def run_autofit(project, parset_name, maxtime=60):
    project.autofit(
        name='{}_copy'.format(parset_name),
        orig=parset_name,
        maxtime=maxtime
    )
