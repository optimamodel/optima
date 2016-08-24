from fabric.api import hosts, run, sudo, env

env.hosts = ['athena.optimamodel.com']


def service_restart(service):

    sudo('service %scelery stop' % (service,))
    sudo('service %s restart' % (service,))


def service_logs(service, follow=True):

    if follow:
        sudo('journalctl -u %s -f' % (service,))
    else:
        sudo('journalctl -u %s -n 100' % (service,))


def restart_rproxy():

    sudo('service rproxy restart')
