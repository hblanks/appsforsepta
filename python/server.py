#!/usr/bin/env python

import gevent.monkey
gevent.monkey.patch_all()

import os.path
import urllib2

import cherrypy
import gevent.wsgi

import transitview
import tripplanner

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    'server.conf')

class Root(object):
    transitview = transitview.TransitViewProxy()
    tripplanner = tripplanner.TripPlannerJsonProxy()

app = cherrypy.tree.mount(
    Root(), '/', config=CONFIG_PATH)
gevent.wsgi.WSGIServer(('', 8000), app).serve_forever()
