# finn.py
"""
This file contains a test of using the finnhub.io database (which is an industrial class database)

This looks pretty good - goes back a long ways and has lots of small company tickers.

The only issue is that it costs $50 per month.  Is it worth it?

"""

# Get the required packages
import pandas as pd
import numpy as np
import requests
import json

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

api_key = 'btgmrsv48v6thhaqgrtg'
function = 'metric'
symbol = 'MNTX'

# Set up the url to get the data
base_url = 'https://finnhub.io/api/v1'

# full query string
query = f'{base_url}/stock/{function}?symbol={symbol}&token={api_key}'

r = requests.get(query)



