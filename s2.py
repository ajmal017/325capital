#! /usr/bin/env python3
# This file attempts to calucalte an earings power and return to current price
# it collects data from both screen1.get_fscore and complete financials from FundamentalAnalysis

from screen1 import *
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import itertools
import FundamentalAnalysis as fa
import sys
from sklearn.linear_model import LinearRegression


# Set up some convenience settings
pd.set_option('display.max_rows', 200)
pd.set_option('display.max_seq_items', 200)

# use the 325 style
plt.style.use('325')


# Get the latst fscores from fscores.xlsx
# This sheet is populated using build_fscores_excel.py
# It also uses Fundamental Analysis toolkit so have the api_key ready
api_key = "c350f6f5a4396d349ee4bbacde3d5999"
filenames = ['fscores.xlsx']
sheets = {'Sheet1':[0, 'A:DO', 1612]}
d = getasheet(filenames, sheets, 'symbol')

# Split out the most wanted sectors
short_sector_wanted = ['TMT',
 'Healthcare',
 'Industrials',
 'Consumer Cyclical',
 'Commercial Service',
 'Technology',
 'Construction',
 'Communication Services',
 'Consumer Product',
 'Utilities',
 'Retail',
 'Consumer Defensive']

short_sector_not_wanted = ['Financial Services',
        'Ag Chem and Materials',
        'Energy',
        'Basic Materials',
        'Real Estate'
        ]

sector_not_wanted = ['Biotechnology',
        'Capital Markets'
        ]

# screen for wanted spaces
b = d[d.short_sector.isin(short_sector_wanted)]
b = b[~b.sector.isin(sector_not_wanted)]

# screeners for 235 actives
actives = b[b.last_work == 'Active']

# what ticker do you want to calculate for?
# ticker = sys.argv[1]
ticker = 'ATRO'

# grab the score for the ticker in question
score = d.loc[ticker]

# Get the financials for the ticker in question. Focus on annuals for now
inc = fa.income_statement(ticker, api_key, 'annual').T
inc.index = pd.to_datetime(inc.index)
inc.sort_index(inplace = True)
inc.revenue  = inc.revenue.replace(0, np.nan).interpolate() # inc

bs = fa.balance_sheet_statement(ticker, api_key, 'annual').T
bs.index = pd.to_datetime(bs.index)
bs.sort_index(inplace = True)
bs['wc'] = (bs.totalCurrentAssets - bs.cashAndShortTermInvestments) - bs.totalCurrentLiabilities

cf = fa.cash_flow_statement(ticker, api_key, 'annual').T
cf.index = pd.to_datetime(cf.index)
cf.sort_index(inplace = True)

# Create a down case scenario clamp growth at 10% for scenario to be more conservative
last_recession_cagrs = inc.revenue.pct_change(1)['2009':'2013']
# revenue_scenario = [i if i < .1 else .1 for i in last_recession_cagrs]
revenue_scenario = [-.25, .05, .05,.05,.05]

forecast, inputs = get_ep(ticker = ticker, inc = inc, bs = bs, cf = cf, revenue_scenario = revenue_scenario)

# make df easier to handle with columns
forecast = forecast.T

# Create some interesting variables
sell_price = forecast.value_per_share[5]
ep_irr = ((sell_price / score.price) ** (1 / 5) ) - 1
buy_price_ten_percent = sell_price / ((1 + .1) ** 5)
implied_ebitda_multiple = forecast.ev[5] / forecast.ebitda[5]
value_from_tv_percent = forecast.tv_value_in_year[5] / forecast.ev[5]

# Create some data to graph from history to forecast to compare realism
forecast.index = pd.date_range(start = '2019-01-01', periods = 11, freq = 'Y')
r = inc.revenue / 1e6
# Don't include 2019 in forecast line items so start at [1:], not [0:]
r = r.append(forecast.revenue[1:])
# measure sga as all costs other than cost of goods to ebitda
s = inc.grossProfit - inc.ebitda
s = s/1e6
s = s.append(forecast.sga[1:])
c = inc.costOfRevenue / 1e6
c = c.append(forecast.cogs[1:])
e = inc.ebitda / 1e6
e = e.append(forecast.ebitda[1:])
g = inc.grossProfit / 1e6
g = g.append(forecast.gm[1:])
# get margins
em = e / r
gm = g / r
#make a table

fig = plt.figure(constrained_layout = True)
gs = fig.add_gridspec(2,2)
fig.suptitle(ticker + "\n" + "{} {}".format(score.business, score.price))

ax1 = fig.add_subplot(gs[0,0:2])
g1 = series_line(ax = ax1, data_label = "r cagr", values = r.pct_change(1), title = 'financials', percent = True)
g1 = series_line(ax = ax1, data_label = "gm", values = gm, title = 'financials', percent = True)
g1 = series_line(ax = ax1, data_label = "em", values = em, title = 'financials', percent = True)


ax2 = fig.add_subplot(gs[1,0])
g = series_bar(ax = ax2, data_labels = ['sell price', 'buy_price (10%)', 'implied ebitda_multiple', ], values = [sell_price, buy_price_ten_percent, implied_ebitda_multiple], title = 'key ep measures', percent = False)

ax3 = fig.add_subplot(gs[1,1])
g2 = series_bar(ax = ax3, data_labels = ['irr', 'tv percent of value'], values = [ep_irr, value_from_tv_percent], title = 'key ep diagnostics', percent = True)



