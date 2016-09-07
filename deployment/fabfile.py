"""
Scripts for running certain procedural tasks on Athena (restarting services,
viewing logs).
"""

from __future__ import absolute_import, division

from fabric.api import hosts, run, sudo, env, cd

# The hosts that you want to run these scripts on
# Right now -- just athena
env.hosts = ['athena.optimamodel.com']


def optima_restart(service):
    """
    Restart an Optima service. This will automatically restart its celery
    instance, if it has one.
    """
    sudo('systemctl daemon-reload')
    try:
        sudo('service %scelery stop' % (service,))
    except:
        pass
    sudo('service %s restart' % (service,))


def optima_regenerate_frontend(service):
    """
    Regenerate the front-end files of an Optima service.
    """
    with env(user="optima"):
        with cd("/home/optima/installations/%s/client" % (service,)):
            run('clean_dev_build.sh')


def service_logs(service, follow=True):
    """
    View the logs of a particular service.

    If `follow` is True, it will follow the log (like `tail -f`), else it will
    print the last 100 lines and quit.
    """
    if follow is True:
        sudo('journalctl -u %s -f' % (service,))
    else:
        sudo('journalctl -u %s -n 100' % (service,))


def rproxy_restart():
    """
    Restart the rproxy service.
    """
    sudo('service rproxy restart')
