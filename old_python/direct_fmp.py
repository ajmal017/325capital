#!/usr/bin/env python

try:
    import json
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

api_key = "c350f6f5a4396d349ee4bbacde3d5999"


def get_fmp_data(statement):
    """
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    statement : str which is the financial modeling prep statement you want
    examples are :
         - balance-sheet-statement
         - balance-sheet-statement-as-reported
         - income-sheet-statement
         - ratios
         - cash-flow-statement

    Returns
    -------
    dict
    """
    ticker = 'EBIX'
    target = "https://financialmodelingprep.com/api/v3/"
    url = target + statement + '/' + ticker + '?apikey=' + api_key
    response = urlopen(url)
    data = response.read().decode("utf-8")

    return json.loads(data)
