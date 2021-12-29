import uuid
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from constants import cmc_key
from constants import cmc_web_cookie_key
import cmcpaths as CMCPaths
import time
from datetime import datetime
import math


class RenderJSON(object):
    def __init__(self, json_data):
        if isinstance(json_data, dict) or isinstance(json_data, list):
            self.json_str = json.dumps(json_data)
        else:
            self.json_str = json_data
        self.uuid = str(uuid.uuid4())

    def _ipython_display_(self):
        display_html('<div id="{}" style="height: 600px; width:100%;font: 12px/18px monospace !important;"></div>'.format(self.uuid), raw=True)
        display_javascript("""
        require(["https://rawgit.com/caldwell/renderjson/master/renderjson.js"], function() {
            renderjson.set_show_to_level(2);
            document.getElementById('%s').appendChild(renderjson(%s))
        });
      """ % (self.uuid, self.json_str), raw=True)


def getEpochTime(datetime): 
    pattern = '%d.%m.%Y %H:%M:%S'
    epoch = int(time.mktime(time.strptime(datetime, pattern)))
    return epoch

def getEpochTimeNow():
    now = datetime.now()
    now = now.strftime("%d.%m.%Y %H:%M:%S")
    return getEpochTime(now)

def convertISODateTimeToEpoch(target):
    utc_time = datetime.strptime(target, "%Y-%m-%dT%H:%M:%S.%fZ")
    epoch_time = (utc_time - datetime(1970, 1, 1)).total_seconds()
    return math.ceil(epoch_time)

DATE_ONE_DAY_DURATION = 24*60*60