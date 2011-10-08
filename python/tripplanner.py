
import gevent.monkey
gevent.monkey.patch_all()

import datetime
import json
import time
import urllib
import urllib2

import cherrypy
import gevent
import lxml.etree
import lxml.html
import pytz
from lxml.cssselect import CSSSelector

import lxutils

############################### Constants ##############################

LOCAL_TZ = pytz.timezone('America/New_York')

QUERY_URL = 'http://airs1.septa.org/bin/query.exe/en'

step_1_form_sel = CSSSelector('form#HFSQuery')

step_2_form_sel = CSSSelector('form#HFSResult')

tp_details_sel = CSSSelector('table.resultTable tr.tpDetails')

td_first_station_sel = CSSSelector('td.first.station')
td_time_arr_sel = CSSSelector('td.timeArr')
td_time_dep_sel = CSSSelector('td.timeDep')
td_products_sel = CSSSelector('td.products')
td_remarks_sel = CSSSelector('td.remarks')

TD_CLASS_MAPPING = {
    'first station': td_first_station_sel,
    'timeArr': td_time_arr_sel,
    'timeDep': td_time_dep_sel,
    'products': td_products_sel,
    'remarks': td_remarks_sel,
    }


################################ Helpers ###############################

def get_form_action(lx, sel):
    forms = sel(lx)
    if not forms:
        raise Exception('No form found in output')
    return forms[0].attrib['action']

def format_local_time(fmt):
    return LOCAL_TZ.fromutc(datetime.datetime.now()).strftime(fmt)

################################ Parsers ###############################

def yield_tr_chunks(trs):
    """
    Takes an iterable of <tr> elements. Yields them back chunked
    into one group for each trip.
    """
    chunk = None
    for tr in trs:
        if tr.find('./th') is not None:
            if chunk is not None:
                yield chunk
            chunk = []
        else:
            chunk.append(tr)

    if chunk is not None:
        yield chunk

def parse_tr(tr):
    raw_dict = dict(
        (k, lxutils.lx_and_sel_to_text(tr, sel))
        for k, sel in TD_CLASS_MAPPING.iteritems()
        )
    return dict(
        (k, v) for k, v in raw_dict.iteritems() if v is not None
        )

def parse_tr_chunk(trs):
    current_step = {}
    for tr in trs:
        d = parse_tr(tr)
        # TODO: parse times?
        if tr.attrib['class'].endswith(' first'):
            current_step['from'] = d['first station']
            current_step['departure_time'] = d['timeDep']
            current_step['service'] = d['products']
        elif tr.attrib['class'].endswith(' last'):
            current_step['to'] = d['first station']
            current_step['arrival_time'] = d['timeArr']
            yield current_step
            current_step = {}

############################ Core functions ############################

# SALL	1
# ZALL	1
# date	10/08/11
# getstop	1
# s	4500 osage ave, philadelphia, pa 19143 USA?
# time	3:25 PM
# timesel	depart
# z	broad and south?
def submit_step_1(origin, destination):
    """
    Takes an origin and destination string. Returns...
    """
    querydict = {
        's': origin,
        'z': destination,
        'time': format_local_time('%I:%M %p'),
        'getstop': '1',
        'SALL': '1',
        'ZALL': '1',
        'timesel': 'depart'
        }

    query = urllib.urlencode(querydict)
    url = '%s?%s' % (QUERY_URL, query)
    lx = lxml.html.parse(urllib2.urlopen(url))
    return get_form_action(lx, step_1_form_sel)

# ident	id.0263811.1318103047
# seqnr	1
# {'guiVCtrl_connection_detailsOut_select_C1-0': ['yes'],
#  'jumpToDetails=yes&guiVCtrl_connection_detailsOut_add_group_overviewOut': ['Details for all'],
#  'sortConnections': ['minDeparture'],
#  'test0': ['x']}
# {'FareClass': ['1'],
#  'REQ0HafasSearchForw': ['1'],
#  'REQ0HafasUnsharpSearch': ['1'],
#  'REQ0JourneyDate': ['Sa, 10/08/2011'],
#  'REQ0JourneyProduct_prod_list': ['1:1111000000000000'],
#  'REQ0JourneyStopsS0A': ['255'],
#  'REQ0JourneyStopsS0K': ['S-0G51'],
#  'REQ0JourneyStopsZ0A': ['1'],
#  'REQ0JourneyStopsZ0K': ['S-1N1'],
#  'REQ0JourneyTime': ['08:20 PM'],
#  'queryPageDisplayed': ['yes'],
#  'start': ['Plan my trip'],
#  'tariffViewMode': ['NONE'],
#  'wDayExt0': ['Mo|Tu|We|Th|Fr|Sa|Su']}

def submit_step_2(url):
    querydict = {
        'FareClass': '1',
        'REQ0HafasSearchForw': '1',
        'REQ0HafasUnsharpSearch': '1',
        'REQ0JourneyDate': '%s, %s' % (
            format_local_time('%a'), format_local_time('%m/%d/%Y')
            ),
        'REQ0JourneyProduct_prod_list': '1:1111000000000000',
        'REQ0JourneyStopsS0A': '255',
        'REQ0JourneyStopsS0K': 'S-0G51',
        'REQ0JourneyStopsZ0A': '1',
        'REQ0JourneyStopsZ0K': 'S-1N1',
        'REQ0JourneyTime': format_local_time('%I:%M %p'),
        'queryPageDisplayed': 'yes',
        'start': 'Plan my trip',
        'tariffViewMode': 'NONE',
        'wDayExt0': 'Mo|Tu|We|Th|Fr|Sa|Su'
        }
    data = urllib.urlencode(querydict)
    cherrypy.log(url)
    lx = lxml.html.parse(urllib2.urlopen(url, data))
    with open('/usr/share/nginx/www/foo.html', 'w') as f:
        f.write(lxml.html.tostring(lx))
    next_url = get_form_action(lx, step_2_form_sel)

    querydict = {
        # more stuff...
        'guiVCtrl_connection_detailsOut_select_C1-0': 'yes',
        'jumpToDetails=yes&guiVCtrl_connection_detailsOut_add_group_overviewOut': 'Details for all',
        'sortConnections': 'minDeparture',
        'test0': 'x'
        }
    data = urllib.urlencode(querydict)
    lx = lxml.html.parse(urllib2.urlopen(next_url, data))
    return lx

def parse_step_2(lx):
    result = []
    for chunk in yield_tr_chunks(tp_details_sel(lx)):
        steps = list(parse_tr_chunk(chunk))
        result.append({'steps': steps})
    return result

def get_trips(origin, destination):
    """
    Takes an origin and destination address string. Returns a
    list of possible trips, each of the format:
    
        {'steps': {
            'from': <step start address str>,
            'to': <step end address str>,
            'departs': <step departure time in UTC seconds, int>,
            'arrives': <step departure time in UTC seconds, int>,
            'name': <step route name str>
            }
        }
    """
    cherrypy.log('%s -> %s' % (repr(origin), repr(destination)))
    step_2_url = submit_step_1(origin, destination)    
    lx = submit_step_2(step_2_url)
    return parse_step_2(lx)

############################ Cherrpy Service ###########################

class TripPlannerJsonProxy(object):
    @cherrypy.expose
    def index(self, **kwargs):
        if not kwargs.get('from') or not kwargs.get('to'):
            raise ValueError

        trips = get_trips(kwargs['from'], kwargs['to'])
        trips_json = json.dumps(trips)
        callback = kwargs.get('callback')
        if callback:
            return '%s(%s);' % (callback, trips_json)
        else:
            return trips_json

################################ Testing ###############################

if __name__ == '__main__':
    lx, result = get_trips('4500 osage ave philadelphia, pa 19143', 'broad and south')
    open('/usr/share/nginx/www/foo.html', 'w').write(
        lxml.html.tostring(lx))