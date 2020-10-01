# iex.py
"""
This file contains a test of using the iex database (which is an industrial class database)

financials only go back 4 years; so probably no good. Also looks expensive in the end.
"""

# Get the required packages
import pandas as pd
import numpy as np
import requests
import json

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

api_key = 'ipk_b9ed4a70d0b74cbd846b03997209df24'
function = 'files'
symbol = 'MNTX'

# Set up the url to get the data
base_url = 'https://cloud.iexapis.com/stable/'

# full query string
query = f'{base_url}{function}/{symbol}'

r = requests.get(query)



