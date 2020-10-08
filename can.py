#! /usr/bin/env python3
"""
This file attempts to use the canalyst api that they have given us
access to as of Oct 5, 2020. Note Canalyst displays a token only once and
thereafter shows a "token ID."  Do not get fooled, use the real token.
"""

# Required packages to interact with  api
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# Set up a request
token ='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VybmFtZSI6ImFzaHJpdmFzdGF2YSIsImVtYWlsIjoiYXNocml2YXN0YXZhQDMyNWNhcGl0YWwuY29tIiwiZmlyc3RfbmFtZSI6IkFuaWwiLCJsYXN0X25hbWUiOiJTaHJpdmFzdGF2YSIsImNvbXBhbnlfbmFtZSI6IjMyNSBDYXBpdGFsIiwiaXNfc3VwZXJ1c2VyIjpmYWxzZSwiaXNfc3RhZmYiOmZhbHNlLCJpc19zeW50aGV0aWMiOmZhbHNlLCJpc19jb2xsZWN0aXZlIjpmYWxzZSwidXNlcl91dWlkIjoiYmY1ZGRmNjctMjBhNC00MTc4LThjNjYtNTlhOGYzMDQ5ZGYyIiwiaWF0IjoxNjAxOTM2MDczLCJpc3MiOiJhcHAuY2FuYWx5c3QuY29tIiwidHlwZSI6ImFwcGxpY2F0aW9uIiwidXVpZCI6IjMyODZkZWRmLTVjYzktNGJiNy04MTRjLTI0OWIxZWIyMjUyZiJ9.huaTYZWul7ZSvK5KHSBBA9wELE12Me5_JQCdB9wm1MU'

def get_csin_and_model_for_ticker(ticker):
    ticker = ticker.upper()
    ticker = ticker+' US'

    base_url = 'https://mds.canalyst.com/api'

    # Authentication string
    headers = {'Authorization': f'Bearer {token}'}

    # Set up to get company list
    endpoint_path = '/equity-model-series/'

        # Parameters to pass
    params = {'page_size': 200,
            'company_ticker_bloomberg': ticker,
            }

        # Get the page
    target_url = base_url + endpoint_path
    r = requests.get(
            target_url,
            headers = headers,
            params = params,
            )

    return r.json()['results'][0]['csin'], r.json()['results'][0]['latest_equity_model']['model_version']['name']

def get_historical_data(csin, model_version):

    base_url = 'https://mds.canalyst.com/api'

    # Authentication string
    headers = {'Authorization': f'Bearer {token}'}

    # Set up to get company list
    endpoint_path = f'/equity-model-series/{csin}/equity-models/{model_version}/historical-data-points/'

    # Parameters to pass
    params = {'page_size': 500,
            'csin': csin,
            }

    # Create a df to collect data in
    dff = pd.DataFrame()
    dfq = pd.DataFrame()

    # Get the page
    while (True):

        target_url = base_url + endpoint_path
        r = requests.get(
                target_url,
                headers = headers,
                params = params,
                )

        # Grab the key fields from results
        d = pd.json_normalize(r.json()['results'])

        # Grab the next link
        target_url = r.json()['next']

        # Now convert d into something that has normal fields by date index
        d.value = pd.to_numeric(d.value)
        normal = pd.pivot_table(d, values = 'value', index = 'period.name', columns = 'time_series.slug')
        # Convert dates to pandas type dates and split dataframes into quarterlies and fiscals
        q = normal[normal.index.str.startswith('Q')].copy()
        f = normal[normal.index.str.startswith('F')].copy()
        q.index = q.index.str.split('-').str.get(1) +  q.index.str.split('-').str.get(0)
        f.index = f.index.str.replace('FY', '')


        # Add what we have to our saver dataframes
        dff = pd.concat([dff,normal], axis = 'columns')
        dfq = pd.concat([dfq,normal], axis = 'columns')

        print(target_url, dff, dfq)
        if target_url == 'null':
            break

    return dff, dfq

def get_can_series(ticker, field = 'MO_RIS_REV'):

    csin, model_version = get_csin_and_model_for_ticker(ticker)

    base_url = 'https://mds.canalyst.com/api'

    # Authentication string
    headers = {'Authorization': f'Bearer {token}'}

    # Set up to get company list
    endpoint_path = f'/equity-model-series/{csin}/equity-models/{model_version}/historical-data-points/'

    # Parameters to pass
    params = {'page_size': 500,
            'csin': csin,
            'model_version': model_version,
            'time_series_name': field
            }

    target_url = base_url + endpoint_path
    r = requests.get(
            target_url,
            headers = headers,
            params = params,
            )

    # Grab the key fields from results
    d = pd.json_normalize(r.json()['results'])

    # Return -1 if field is not found
    if d.empty:
        print(f"Can't find the field you requested to for {ticker}")
        print(f"For debugging purposes csin and model number are: {csin} and {model_version}")
        print(f"Target url is : {target_url}")
        print(f"Return response is : {r.json()}")
        return -1

    # Catch if the untis can be converted to millions or should stay as is
    indollars = d['time_series.unit.symbol'].str.contains('$')
    d.value = d.value.astype(np.float)
    d.value = d[indollars].value / 1e6

    d = d.set_index('period.name')

    # Convert dates to pandas type dates and split dataframes into quarterlies and fiscals
    q = d[d.index.str.startswith('Q')].copy()
    f = d[d.index.str.startswith('F')].copy()
    q.index = q.index.str.split('-').str.get(1) +  q.index.str.split('-').str.get(0)
    f.index = f.index.str.replace('FY', '')

    # Convert index to real pandas datetime
    q.index = pd.to_datetime(q.index)
    f.index = pd.to_datetime(f.index)

    return q.value ,f.value


