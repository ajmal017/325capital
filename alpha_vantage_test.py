# alpha_vantage_test.py
"""
This file contains a test of using the alpha_vantage stock data database
"""

# Get the required packages
import pandas as pd
import numpy as np

# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

api_key = 'ZVBKCPRLCS747H8M'
function = 'OVERVIEW'
symbol = 'MNTX'

# Set up the url to get the data
base_url = 'https://www.alphavantage.co/query?'

# full query string
query = f'{base_url}function={function}&symbol={symbol}&apikey={api_key}'


