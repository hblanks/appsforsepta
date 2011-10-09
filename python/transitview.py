
import cherrypy
import urllib2

ROOT_URL = 'http://www3.septa.org/transitview/bus_route_data/'

class TransitViewProxy(object):
    """
    JSONP proxy for transitview.
    """

    @cherrypy.expose
    def bus_route_data(self, route, callback=None):
        """
        Simple JSONP passthrough for transitview/bus_route_data/.
        """
        data = urllib2.urlopen('%s/%s' % (ROOT_URL, route)).read()
        if callback is None:
            return data
        else:
            return '%s(%s);' % (callback, data)
