#!/usr/bin/env python

from gevent.pywsgi import WSGIServer
from wsgi import app

server = WSGIServer(('', 8080), app, log=None)
server.serve_forever()