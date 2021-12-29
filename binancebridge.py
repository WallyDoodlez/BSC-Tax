import json
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def list_args_to_comma_separated(func):
    """Return function that converts list input arguments to comma-separated strings"""
    def input_args(*args,**kwargs):
        for v in kwargs:
            # check in **kwargs for lists and convert to comma-separated string
            if isinstance(kwargs[v], list): kwargs[v]=','.join(kwargs[v])
        # check in *args for lists and convert to comma-separated string
        args=[','.join(v) if isinstance(v, list) else v for v in args]
        return func(*args, **kwargs)
    return input_args


class BinanceBridgeAPI:
    __API_URL_BASE = ' https://api.binance.org/bridge/api/v2/'

    
    def __init__(self, api_base_url=__API_URL_BASE):
        self.api_base_url = api_base_url
        self.request_timeout = 120

        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def __request(self, url):
            # print(url)
        try:
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()
            content = json.loads(response.content.decode('utf-8'))
            return content
        except Exception as e:
            # check if json (with error message) is returned
            try:
                content = json.loads(response.content.decode('utf-8'))
                raise ValueError(content)
            # if no json
            except json.decoder.JSONDecodeError:
                pass
            # except UnboundLocalError as e:
            #    pass
            raise

    def __api_url_params(self, api_url, params):
        if params:
            api_url += '?'
            for key, value in params.items():
                api_url += "{0}={1}&".format(key, value)
            api_url = api_url[:-1]
        return api_url


    @list_args_to_comma_separated
    def get_tokens(self, **kwargs):
        """Get all the tokens supported in Binance bridge"""

        api_url = '{0}tokens'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)
