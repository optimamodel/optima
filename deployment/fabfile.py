from fabric.api import hosts, run, sudo, env

env.hosts = ['athena.optimamodel.com']


def service_restart(service):

    sudo('systemctl daemon-reload')
    try:
        sudo('service %scelery stop' % (service,))
    except:
        pass
    sudo('service %s restart' % (service,))


def service_logs(service, follow=True):

    if follow is True:
        sudo('journalctl -u %s -f' % (service,))
    else:
        sudo('journalctl -u %s -n 100' % (service,))


def restart_rproxy():

    sudo('service rproxy restart')
