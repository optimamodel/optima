import sys
import os

sys.path.append(os.path.abspath("server/"))

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.logger import globalLogBeginner, FileLogObserver, formatEvent
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.wsgi import WSGIResource

globalLogBeginner.beginLoggingTo([
    FileLogObserver(sys.stdout, lambda _: formatEvent(_) + "\n")])

import api

wsgi_app = WSGIResource(reactor, reactor.getThreadPool(), api.app)

class OptimaResource(Resource):
    isLeaf = True

    def __init__(self, wsgi):
        self._wsgi = wsgi

    def render(self, request):
        request.prepath = []
        request.postpath = ['api'] + request.postpath[:]
        return self._wsgi.render(request)


base_resource = File('client/source/')
base_resource.putChild('build', File('client/source/'))
base_resource.putChild('api', OptimaResource(wsgi_app))

site = Site(base_resource)

endpoint = serverFromString(reactor, "tcp:port=8080")
endpoint.listen(site)

reactor.run()
