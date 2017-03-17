import sys

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.logger import globalLogBeginner, FileLogObserver, formatEvent
from twisted.web.resource import Resource, EncodingResourceWrapper
from twisted.web.server import Site, GzipEncoderFactory
from twisted.web.static import File
from twisted.web.wsgi import WSGIResource
from twisted.python.threadpool import ThreadPool

from . import api


def run():
    """
    Run the server.
    """
    globalLogBeginner.beginLoggingTo([
        FileLogObserver(sys.stdout, lambda _: formatEvent(_) + "\n")])

    threadpool = ThreadPool(maxthreads=30)
    wsgi_app = WSGIResource(reactor, threadpool, api.app)

    class OptimaResource(Resource):
        isLeaf = True

        def __init__(self, wsgi):
            self._wsgi = wsgi

        def render(self, request):
            request.prepath = []
            request.postpath = ['api'] + request.postpath[:]

            r = self._wsgi.render(request)

            request.responseHeaders.setRawHeaders(
                b'Cache-Control', [b'no-cache', b'no-store', b'must-revalidate'])
            request.responseHeaders.setRawHeaders(b'expires', [b'0'])
            return r
    
    class WrappedFile(File):        
        def getChild(self, path, request):
            child = File.getChild(self, path, request)            
            return EncodingResourceWrapper(child, [GzipEncoderFactory()])

    # From http://stackoverflow.com/questions/5428473/twisted-http-gzip-support

    base_resource = File('client/build/')
    optima_resource = OptimaResource(wsgi_app)
    base_resource.putChild('api', optima_resource)
    
    wrapped = EncodingResourceWrapper(base_resource, [GzipEncoderFactory()])

    site = Site(wrapped)

    try:
        port = str(sys.argv[1])
    except IndexError:
        port = "8080"

    # Start the threadpool now, shut it down when we're closing
    threadpool.start()
    reactor.addSystemEventTrigger('before', 'shutdown', threadpool.stop)

    endpoint = serverFromString(reactor, "tcp:port=" + port)
    endpoint.listen(site)

    reactor.run()

if __name__ == "__main__":
    run()
