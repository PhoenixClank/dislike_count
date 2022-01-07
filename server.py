from gevent.pywsgi import WSGIServer
from werkzeug.middleware.proxy_fix import ProxyFix
from wsgi import app

server = WSGIServer(('', 8080), ProxyFix(app, x_for=1, x_proto=1, x_port=1), log=None)
server.serve_forever()
