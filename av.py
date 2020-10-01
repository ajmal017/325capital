# alpha_vantage_test.py
"""
This file contains a test of using the alpha_vantage stock data database

Based on my trial of it, the data only goes back five years and so not really that useful for us.

I have a query into the company about taht and will udpate
"""

# Get the required packages
import pandas as pd
import numpy as np
import requests
import json

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

api_key = 'ZVBKCPRLCS747H8M'
function = 'INCOME_STATEMENT'
symbol = 'MNTX'

# Set up the url to get the data
base_url = 'https://www.alphavantage.co/query?'

# full query string
query = f'{base_url}function={function}&symbol={symbol}&apikey={api_key}'

r = requests.get(query)



